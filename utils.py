from contextlib import closing
import errno
import os
import socket


# http://stackoverflow.com/a/166589
def get_routed_ip():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        s.connect(("8.8.8.8", 80))  # Google DNS for a reliable host on the internet at large
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
