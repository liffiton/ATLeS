#!/usr/bin/env python

import atexit
import os
import platform
import signal
import socket
import sys
import threading
import time

import rpyc
import zeroconf

from rpyc.utils.server import ThreadedServer

import config
import utils
from fishweb import expmanage


_PORT = 4158


def module2service(module):
    ''' Create a class containing an exposed_[method]() method
    for every public method (callable object not named with a '_')
    in the given module.  This can be passed to RPyC to expose
    all of the modules methods via RPC.
    '''

    # methods is a list of public method *names* (strings)
    methods = [method for method in dir(module) if callable(getattr(module, method)) and not method.startswith('_')]

    # an empty rpyc.Service class to be filled with new methods
    class _serviceclass(rpyc.Service):
        pass

    for method in methods:
        newname = "exposed_%s" % method
        # make it a static method so no one tries to pass it self
        oldmethod = staticmethod(getattr(module, method))
        setattr(_serviceclass, newname, oldmethod)

    return _serviceclass


def term_handler():
    sys.exit(1)


def main():
    # catch SIGTERM (e.g., from start-stop-daemon)
    signal.signal(signal.SIGTERM, term_handler)

    # Create needed directories if not already there
    utils.mkdir(config.PLOTDIR)
    utils.mkdir(config.TRACKDIR)
    utils.mkdir(config.DBGFRAMEDIR)
    utils.mkdir(config.ARCHIVEDIR)

    # Get our external IP
    # Loop until we have one, because we can't run without it
    ip = None
    while ip is None:
        try:
            ip = utils.get_routed_ip()
        except:
            # any error (in part because I'm not certain what is thrown
            # when this fails)
            ip = None
            # wait 5 seconds between attempts, assuming we're waiting
            # for the network to come up
            time.sleep(5)

    # make expmanage RPyC-able
    service = module2service(expmanage)
    # and RPyC it
    try:
        server = ThreadedServer(service, hostname='localhost', port=_PORT, protocol_config={"allow_public_attrs": True})
    except socket.error as e:
        print("Error opening socket.  fishremote may already be running.")
        print(e)
        sys.exit(1)

    # ThreadedServer launches threads for incoming connections, but its main accept() loop is blocking,
    # so we put it in a separate thread.
    serverthread = threading.Thread(target=server.start)
    serverthread.daemon = True
    serverthread.start()
    atexit.register(server.close)

    print("RPC server started.")

    # register the service via MDNS/Bonjour
    boxname = platform.node()
    info = zeroconf.ServiceInfo(
        "_fishbox._tcp.local.",
        "%s._fishbox._tcp.local." % boxname,
        socket.inet_aton(ip), _PORT, 0, 0,
        {
            'name': boxname,
            'appdir': os.getcwd(),
            'user': config.FISHREMOTE_USER
        }
    )
    zconf = zeroconf.Zeroconf([ip])
    zconf.register_service(info)
    atexit.register(zconf.unregister_service, info)

    print("Service registered: %s port %d" % (ip, _PORT))

    # wait until the server is done
    if sys.version_info[0] >= 3:
        serverthread.join()
    else:
        # In Python 2, a timeout is required for join() to not just
        # call a blocking C function (thus blocking the signal handler).
        # However, infinity works.
        serverthread.join(float('inf'))


if __name__ == '__main__':
    main()
