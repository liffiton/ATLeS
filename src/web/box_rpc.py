import copy
import datetime
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
from web import db_schema
from common import auto_restart, get_routed_ip, max_mtime


class Box(object):
    def __init__(self, name, ip, port, properties, deregister_callback):
        self.name = name   # name of remote box
        self.ip = ip       # IP address
        self.port = port   # port on which atles_remote.py is accepting connections

        # callback function for this box to deregister itself w/ zeroconf
        self.deregister_callback = deregister_callback

        # information on git commit status for remote code
        self.gitshort = properties[b'gitshort'].decode()
        self.gitlong = properties[b'gitlong'].decode()

        # does this box have a display for "background images"
        self.hasdisplay = properties[b'hasdisplay']
        # username for SSH login to remote box
        self.user = properties[b'user'].decode()

        # paths to track data directories on remote box
        self.appdir = properties[b'appdir'].decode()
        # build useful paths (assumes same directory structure on remote)
        self.trackdir = self.appdir / config.TRACKDIR.relative_to(config.BASEDIR)
        self.archivedir = self.appdir / config.ARCHIVEDIR.relative_to(config.BASEDIR)
        self.dbgframedir = self.appdir / config.DBGFRAMEDIR.relative_to(config.BASEDIR)

        self.error = None  # Internal error message, if any
        self.local = None  # True if box is actually the local machine

        self._tunnel = None  # SSH tunnel instance
        self._rpc = None     # RPC connection instance

    def get_info(self):
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
            # verify that we actually are connected
            self._ping(timeout=2)

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
        self.local = (self.ip == get_routed_ip())
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

    def down(self, error=None):
        if self._rpc:
            try:
                self._rpc.close()
            except AttributeError:
                pass  # always throws one in Session.close()... bug?
            self._rpc = None
        if self._tunnel:
            self._tunnel.close()
            self._tunnel = None

        self.error = error

    def sync_data(self):
        ''' Copy/sync track data from this box to the local track directory.'''
        print("{}: Starting sync.".format(self.name))

        assert self.connected

        # If data is already local, no need to sync
        assert not self.local

        # Double-check that this box isn't running an experiment
        if self.lock_exists():
            return

        # Copy remote files into an archive dir, then have rsync
        # delete the originals after the transfer
        cp_cmd = self._tunnel["cp"]
        res = cp_cmd("-r", self.trackdir, self.archivedir)
        print("{}: cp command got: {}".format(self.name, res))
        # Currently does *not* copy the debugframes (following line is
        # commented), so they will be removed from remote entirely.
        #cp_cmd("-r", self.dbgframedir, self.archivedir)

        # NOTE: Source must end with / to copy the *contents* of the folder
        # instead of copying the source folder into the destination as a new
        # folder there.
        cmd = ['rsync', '-rvt', '--remove-source-files', '%s@%s:%s/' % (self.user, self.ip, self.trackdir), str(config.TRACKDIR / self.name)]
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print("{}: rsync trackfiles command got: {}".format(self.name, res))

        cmd = ['rsync', '-rvt', '--remove-source-files', '%s@%s:%s/' % (self.user, self.ip, self.dbgframedir), str(config.DBGFRAMEDIR / self.name)]  # '' to ensure trailing /
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        print("{}: rsync dbgframes command got: {}".format(self.name, res))

    def _ping(self, timeout):
        '''
        Attempt to call a function on the server over this connection with a
        given timeout (in seconds).
        '''
        def timeout_close():
            self.down("server timed out; connection closed")
            # The server didn't deregister itself, so we need to here
            # so that zeroconf will properly add the service when it returns.
            self.deregister_callback()

        timer = threading.Timer(timeout, timeout_close)
        timer.start()
        try:
            self.lock_exists()  # any simple function call; return ignored
        finally:
            timer.cancel()

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
        self._browser = ServiceBrowser(zeroconf, "_atlesbox._tcp.local.", self)  # starts its own daemon thread

        # start separate thread for:
        #  - polling boxes
        t = threading.Thread(target=auto_restart(self._poll_boxes))
        t.daemon = True
        t.start()
        #  - handling the explicit update queue
        t = threading.Thread(target=auto_restart(self._watch_queue))
        t.daemon = True
        t.start()

    def add_service(self, zeroconf, type, name):
        ''' Called automatically by ServiceBrowser. '''
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s" % (name, info))
        boxname = info.properties[b'name'].decode()
        assert boxname == name.split('.')[0]

        # make a function for deregistering this box
        def deregister():
            # Do just enough to make zeroconf register the service
            # when it returns.
            # (This is used when a box losesconnection without
            # deregistering itself.)
            del self._browser.services[info.name.lower()]

        newbox = Box(name=boxname,
                     ip=socket.inet_ntoa(info.address),
                     port=info.port,
                     properties=info.properties,
                     deregister_callback=deregister
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

    def _update_box_db(self, box, boxinfo, conn):
        # add current time to boxinfo
        boxinfo['last_updated'] = time.time()

        boxes = db_schema.boxes
        # check whether this box is in the database yet
        select = sql.select([boxes.c.name]).where(boxes.c.name == box)
        box_exists = conn.execute(select).scalar()
        if box_exists:
            # if so, update
            update = boxes.update().where(boxes.c.name == box).values(boxinfo)
            conn.execute(update)
        else:
            # if not, insert
            insert = boxes.insert(boxinfo)
            conn.execute(insert)

    def _update_box_datafiles(self, box, boxinfo, conn):
        ''' Checks for newer datafiles; syncs if any are found. '''
        box_rpc = self._boxes[box]
        # Get mtimes of latest remote and local data files
        latest_remote = box_rpc.max_datafile_mtime()
        if latest_remote is None:
            # No files present on remote
            return
        boxtrackdir = config.TRACKDIR / box
        latest_local = max_mtime(boxtrackdir)

        # *Ugly* hack to "de-netref" the rpyc-returned object
        # Otherwise we can't compare it to a real datetime object...
        timetuple = list(latest_remote.timetuple())[:6]
        timetuple.append(latest_remote.microsecond)
        latest_remote = datetime.datetime(*timetuple)

        # If remote has newer, sync and update latest local time
        if latest_local is None or latest_local < latest_remote:
            box_rpc.sync_data()

        # check that update occurred
        diff = abs(latest_remote - max_mtime(boxtrackdir))
        if diff > datetime.timedelta(seconds=1):
            # warn w/ simple print for now
            print("Warning: sync may not have occurred for box {}.  Got time delta {}.".format(box, diff))

    def _update_box(self, box, conn):
        # get updated box data
        with self._boxlock:
            if box in self._boxes:
                boxinfo = self._boxes[box].get_info()
            else:
                boxinfo = {'connected': False}
        self._update_box_db(box, boxinfo, conn)
        if boxinfo['connected'] \
                and not boxinfo['local'] \
                and not boxinfo['exp_running'] \
                and self._boxes[box].connected \
                and not self._boxes[box].lock_exists():
            self._update_box_datafiles(box, boxinfo, conn)

    def _watch_queue(self):
        # Runs in its own thread
        # Needs a separate sqlite connection for a separate thread
        conn = self._engine.connect()
        while True:
            box = self._updatequeue.get()
            self._update_box(box, conn)

    def _poll_boxes(self):
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
                self._updatequeue.put(box)
            time.sleep(2)
