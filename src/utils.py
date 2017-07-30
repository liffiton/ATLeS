import datetime
import errno
import os
import platform
import socket
from collections import namedtuple

from contextlib import closing

import plumbum


# define a named tuple for storing Phase data
Phase = namedtuple('Phase', ['phasenum', 'length', 'dostim', 'background'])
# Give the named tuple default values [https://stackoverflow.com/a/18348004/7938656]
Phase.__new__.__defaults__ = (None,) * len(Phase._fields)


# http://stackoverflow.com/a/166589
# Create a UDP socket to the internet at large to get our routed IP
def get_routed_ip():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        s.connect(("8.8.8.8", 53))  # Google DNS, but doesn't really matter
        return s.getsockname()[0]


def get_boxname():
    return platform.node()


def mkdir(path):
    try:
        os.makedirs(str(path))
    except OSError as e:
        if e.errno == errno.EEXIST and path.is_dir():
            # exists already, fine.
            pass
        else:
            raise


def git_status():
    git = plumbum.local["git"]
    branch = git('describe', '--contains', '--all', 'HEAD').strip()
    fulldesc = git('describe', '--all', '--long', '--dirty').strip()
    fulldate = git('show', '-s', '--format=%ci').strip()
    date = fulldate.split()[0]
    mods = git['diff', '--no-ext-diff', '--quiet'] & plumbum.TF(1)

    # short git description: date plus dirty marker
    gitshort = "%s-%s%s" % (branch, date, '-*' if mods else '')
    gitlong = "%s\n%s" % (fulldesc, fulldate)
    return (gitshort, gitlong)


def max_mtime(dir):
    files = list(dir.glob("*"))
    if not files:
        return None
    maxtime = max(os.path.getmtime(str(f)) for f in files)
    return datetime.datetime.fromtimestamp(maxtime)
