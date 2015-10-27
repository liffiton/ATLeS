import atexit
import socket
import zeroconf

import utils


boxname = 'box1'


desc = {'path': '/~paulsm/'}
info = zeroconf.ServiceInfo(
    "_fishbox._tcp.local.",
    "%s._fishbox._tcp.local." % boxname,
    socket.inet_aton(utils.get_routed_ip()), 22, 0, 0,
    {'name': boxname}
)

zeroconf = zeroconf.Zeroconf([utils.get_routed_ip()])
print("Registration of a service, press Ctrl-C to exit...")
zeroconf.register_service(info)
atexit.register(zeroconf.unregister_service, info)

import time
while True:
    time.sleep(0.1)
