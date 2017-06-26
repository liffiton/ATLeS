import os
import subprocess

import plumbum
import rpyc

import config
import utils


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
