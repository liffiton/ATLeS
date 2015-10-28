import atexit
import platform
import socket
import sys
import threading

import rpyc
import zeroconf

from rpyc.utils.server import ThreadedServer

from fishcontrol import expmanage
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

        # Make a new method to be assigned an exposed_* name.
        # Using default value for __oldname param binds method
        # in a way that just putting method into getattr() doesn't.
        def newmethod(self, __oldname=method, *args, **kwargs):
            return getattr(module, __oldname)(*args, **kwargs)

        setattr(_serviceclass, newname, newmethod)

    return _serviceclass


if __name__ == '__main__':
    # make expmanage RPyC-able
    service = module2service(expmanage)
    # and RPyC it
    server = ThreadedServer(service, hostname='localhost', port=port)
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
        {'name': boxname}
    )
    zeroconf = zeroconf.Zeroconf([ip])
    zeroconf.register_service(info)
    atexit.register(zeroconf.unregister_service, info)

    print("Service registered: %s port %d" % (ip, port))

    # wait until the server is done
    if sys.version_info[0] >= 3:
        serverthread.join()
    else:
        # In Python 2, a timeout is required for join() to not just
        # call a blocking C function (thus blocking the signal handler).
        # However, infinity works.
        serverthread.join(float('inf'))
