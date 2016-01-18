import errno
import os
import socket

from contextlib import closing


# http://stackoverflow.com/a/166589
# Create a UDP socket to the internet at large to get our routed IP
def get_routed_ip():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        s.connect(("8.8.8.8", 53))  # Google DNS, but doesn't really matter
        return s.getsockname()[0]


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            # exists already, fine.
            pass
        else:
            raise
