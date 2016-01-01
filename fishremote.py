import atexit
import daemon
import getpass
import os
import platform
import socket
import sys
import threading

import rpyc
import zeroconf

from rpyc.utils.server import ThreadedServer

from fishweb import expmanage
import utils


boxname = platform.node()
ip = utils.get_routed_ip()
port = 4158


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


def run_remote():
    # make expmanage RPyC-able
    service = module2service(expmanage)
    # and RPyC it
    try:
        server = ThreadedServer(service, hostname='localhost', port=port, protocol_config={"allow_public_attrs":True})
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
    info = zeroconf.ServiceInfo(
        "_fishbox._tcp.local.",
        "%s._fishbox._tcp.local." % boxname,
        socket.inet_aton(ip), port, 0, 0,
        {
            'name': boxname,
            'appdir': os.getcwd(),
            'user': getpass.getuser()
        }
    )
    zconf = zeroconf.Zeroconf([ip])
    zconf.register_service(info)
    atexit.register(zconf.unregister_service, info)

    print("Service registered: %s port %d" % (ip, port))

    # wait until the server is done
    if sys.version_info[0] >= 3:
        serverthread.join()
    else:
        # In Python 2, a timeout is required for join() to not just
        # call a blocking C function (thus blocking the signal handler).
        # However, infinity works.
        serverthread.join(float('inf'))


def main():
    if len(sys.argv) > 1:
        # run without going to background/daemonizing
        run_remote()

    print("Switching to background daemon.")
    logfile = os.path.join(
        os.getcwd(),
        "remote.log"
    )
    with open(logfile, 'w+') as log:
        context = daemon.DaemonContext(
            working_directory=os.getcwd(),
            stdout=log,
            stderr=log
        )
        # For python-daemon >= 2.1.0
        context.initgroups = False

        with context:
            run_remote()


if __name__ == '__main__':
    main()
