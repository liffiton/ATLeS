import copy
import os
import socket
import subprocess
import threading
import time

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

import plumbum
import rpyc
from sqlalchemy import sql
from zeroconf import ServiceBrowser, Zeroconf

import config
import utils
from fishweb import db_schema


class Box(object):
    def __init__(self, name, ip, port, properties):
        self.name = name   # name of remote box
        self.ip = ip       # IP address
        self.port = port   # port on which fishremote.py is accepting connections

        # information on git commit status for remote code
        self.gitshort = properties[b'gitshort'].decode()
        self.gitlong = properties[b'gitlong'].decode()

        # does this box have a display for "background images"
        self.hasdisplay = properties[b'hasdisplay']
        # username for SSH login to remote box
        self.user = properties[b'user'].decode()

        # path to track data directory on remote box
        self.appdir = properties[b'appdir'].decode()
        # build useful paths
        self.trackdir = os.path.join(self.appdir, config.TRACKDIR)
        self.archivedir = os.path.join(self.appdir, config.ARCHIVEDIR)
        self.dbgframedir = os.path.join(self.appdir, config.DBGFRAMEDIR)

        self.error = None  # Internal error message, if any
        self.local = None  # True if box is actually the local machine

        self._tunnel = None  # SSH tunnel instance
        self._rpc = None     # RPC connection instance

    def as_dict(self):
        ret = {
            'name': self.name,
            'ip': self.ip,
            'port': self.port,
            'user': self.user,
            'hasdisplay': self.hasdisplay,
            'connected': self.connected,
            'gitshort': self.gitshort,
            'gitlong': self.gitlong,
            'local': self.local,
            'error': self.error,
        }

        if self.connected:
            lock_data = self.lock_data()
            ret.update({
                'exp_running': lock_data.get('running'),
                'exp_pid': lock_data.get('pid'),
                'exp_starttime': lock_data.get('starttime'),
                'exp_runtime': lock_data.get('runtime')
            })
        else:
            ret['exp_running'] = False

        return ret

    def connect(self, done_callback=None):
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
        if done_callback is not None:
            done_callback(self.name)

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
        if name != '_rpc' and self.connected and hasattr(self._rpc.root, name):
            return getattr(self._rpc.root, name)
        else:
            # default behavior
            raise AttributeError


class BoxManager(object):
    def __init__(self, engine):
        self._engine = engine

        self._boxes = dict()
        self._boxlock = threading.Lock()

        self._updatequeue = Queue()

        # work around a bug in zeroconf on Cygwin
        try:
            zeroconf = Zeroconf()
        except socket.error:
            zeroconf = Zeroconf(["0.0.0.0"])
        self._browser = ServiceBrowser(zeroconf, "_fishbox._tcp.local.", self)  # starts its own daemon thread

        # start polling boxes and the queue in separate threads
        t = threading.Thread(target=self.poll_boxes)
        t.daemon = True
        t.start()
        t = threading.Thread(target=self.watch_queue)
        t.daemon = True
        t.start()

    def add_service(self, zeroconf, type, name):
        ''' Called automatically by ServiceBrowser. '''
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s" % (name, info))
        boxname = info.properties[b'name'].decode()
        assert boxname == name.split('.')[0]
        newbox = Box(name=boxname,
                     ip=socket.inet_ntoa(info.address),
                     port=info.port,
                     properties=info.properties
                     )
        # connect in a separate thread so we don't have to wait for the connection here
        threading.Thread(target=newbox.connect, args=[self._updatequeue.put]).start()
        with self._boxlock:
            self._boxes[boxname] = newbox
        self._updatequeue.put(boxname)

    def remove_service(self, zeroconf, type, name):
        ''' Called automatically by ServiceBrowser. '''
        print("Service %s removed" % name)
        boxname = name.split('.')[0]
        with self._boxlock:
            self._boxes[boxname].down()
        self._updatequeue.put(boxname)

    def get_boxes(self):
        with self._boxlock:
            return copy.copy(self._boxes)

    def _update_box(self, box, conn):
        boxes = db_schema.boxes
        # get updated box data
        with self._boxlock:
            if box in self._boxes:
                boxdict = self._boxes[box].as_dict()
            else:
                boxdict = {'connected': False}
        # check whether this box is in the database yet
        select = sql.select([boxes.c.name]).where(boxes.c.name == box)
        box_exists = conn.execute(select).scalar()
        if box_exists:
            # if so, update
            update = boxes.update().where(boxes.c.name == box).values(boxdict)
            conn.execute(update)
        else:
            # if not, insert
            insert = boxes.insert(boxdict)
            conn.execute(insert)

    def watch_queue(self):
        # Runs in its own thread
        # Needs a separate sqlite connection for a separate thread
        conn = self._engine.connect()
        while True:
            box = self._updatequeue.get()
            self._update_box(box, conn)

    def poll_boxes(self):
        # Runs in its own thread
        # Needs a separate sqlite connection for a separate thread
        conn = self._engine.connect()
        boxes = db_schema.boxes
        select = sql.select([boxes.c.name])
        while True:
            # Poll/update all boxes every 2 seconds
            box_names = [row['name'] for row in conn.execute(select)]
            # quick sanity check: all boxes in our list of RPC objects must be registered in the DB
            for box in self._boxes:
                assert box in box_names
            for box in box_names:
                self._update_box(box, conn)
            time.sleep(2)
