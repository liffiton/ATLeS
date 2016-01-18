import copy
import inspect
import os
import socket
import subprocess
import threading

import plumbum
import rpyc
from zeroconf import ServiceBrowser, Zeroconf

import config
import utils


class Box(object):
    def __init__(self, name, ip, port, appdir, user="pi"):
        self.name = name   # name of remote box
        self.ip = ip       # IP address
        self.port = port   # port on which fishremote.py is accepting connections
        self.user = user   # username for SSH login to remote box

        self.appdir = appdir  # path to track data directory on remote box
        # build useful paths
        self.trackdir = os.path.join(self.appdir, config.TRACKDIR)
        self.archivedir = os.path.join(self.appdir, config.ARCHIVEDIR)
        self.dbgframedir = os.path.join(self.appdir, config.DBGFRAMEDIR)

        self.error = None  # Internal error message, if any
        self.local = None  # True if box is actually the local machine

        self._tunnel = None  # SSH tunnel instance
        self._rpc = None     # RPC connection instance

    def as_dict(self):
        return {
            'name': self.name,
            'ip': self.ip,
            'port': self.port,
            'user': self.user,
            'connected': self.connected,
            'local': self.local,
            'error': self.error,
            # called via RPC, lock_data() doesn't return a real dict,
            # so pass it to dict() to make it "real"
            'lock_data': dict(self.lock_data()) if self.connected else dict()
        }

    def connect(self):
        self.error = "connecting..."
        self.local = (self.ip == utils.get_routed_ip())
        if not self.local:
            # only connect if it's a separate machine
            try:
                # -oBatchMode=yes to disable password auth and just fail if key auth fails
                self._tunnel = plumbum.SshMachine(self.ip, user=self.user, ssh_opts=['-oBatchMode=yes'])
            except (plumbum.machines.session.SSHCommsChannel2Error, plumbum.machines.session.SSHCommsError):
                self.error = "SSH connection failure"
                self._tunnel = None
                return

            self._rpc = rpyc.ssh_connect(self._tunnel, self.port)

        else:
            self._rpc = rpyc.connect("localhost", self.port)

        self.error = None

    def down(self):
        if self._rpc:
            self._rpc.close()
            self._rpc = None
        if self._tunnel:
            self._tunnel.close()
            self._tunnel = None
        self.error = None

    def sync_data(self):
        ''' Copy/sync track data from this box to the local track directory.'''
        assert self.connected

        # If data is already local, no need to sync
        assert not self.local

        # Copy remote files into an archive dir, then have rsync
        # delete the originals after the transfer
        self._tunnel["cp -r %s %s" % (self.trackdir, self.archivedir)]
        # Currently does *not* copy the debugframes (following line is
        # commented), so they will be removed from remote entirely.
        #self._tunnel["cp -r %s %s" % (self.dbgframedir, self.archivedir)]

        # Both source and dest must end with / to copy contents of one folder
        # into another, isntead of copying the source folder into the
        # destination as a new folder there.
        # In os.path.join, the '' ensures a trailing /
        cmd = ['rsync', '-rvt', '--remove-source-files', '%s@%s:%s/' % (self.user, self.ip, self.trackdir), os.path.join(config.TRACKDIR, self.name, '')]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)

        cmd = ['rsync', '-rvt', '--remove-source-files', '%s@%s:%s/' % (self.user, self.ip, self.dbgframedir), os.path.join(config.DBGFRAMEDIR, self.name, '')]  # '' to ensure trailing /
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    @property
    def connected(self):
        return self._rpc and not self._rpc.closed

    def __getattr__(self, name):
        '''Return something from self.rpc if it wasn't found in this object
        directly.  Lets us use one object namespace to access both "local"
        methods like sync_data() and remote RPC methods.'''
        if self.connected and hasattr(self._rpc.root, name):
            return getattr(self._rpc.root, name)
        else:
            # default behavior
            raise AttributeError


class BoxManager(object):
    def __init__(self):
        super(BoxManager, self).__init__()
        self._boxes = dict()
        self._boxlock = threading.Lock()

        # work around a bug in zeroconf on Cygwin
        try:
            zeroconf = Zeroconf()
        except socket.error:
            zeroconf = Zeroconf(["0.0.0.0"])
        self._browser = ServiceBrowser(zeroconf, "_fishbox._tcp.local.", self)  # starts its own daemon thread

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s" % (name, info))
        boxname = name.split('.')[0]
        newbox = Box(name=boxname,
                     ip=socket.inet_ntoa(info.address),
                     port=info.port,
                     appdir=info.properties['appdir'],
                     user=info.properties['user'])
        # connect in a separate thread so we don't have to wait for the connection here
        threading.Thread(target=newbox.connect).start()
        with self._boxlock:
            self._boxes[boxname] = newbox

    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % name)
        boxname = name.split('.')[0]
        with self._boxlock:
            self._boxes[boxname].down()

    def get_boxes(self):
        with self._boxlock:
            return copy.copy(self._boxes)


class BoxManagerPlugin(object):
    ''' A plugin to inject a box list from a global BoxManager into any Bottle
    routes that need it (indicated via a "boxes" keyword (customizable)).
    '''

    name = 'boxmanager'
    api = 2

    def __init__(self, kw="boxes"):
        self._boxmanager = BoxManager()
        self._keyword = kw

    def setup(self, app):
        pass

    def close(self):
        pass

    def apply(self, callback, route):
        # Test if the original callback accepts our keyword.
        # Ignore it if it does not need a box list.
        args = inspect.getargspec(route.callback).args
        if self._keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            # inject the box list as a keyword argument
            kwargs[self._keyword] = self._boxmanager.get_boxes()

            return callback(*args, **kwargs)

        # Replace the route callback with the wrapped one
        return wrapper
