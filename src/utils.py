import datetime
import errno
import os
import platform
import pwd
import socket
import time
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


def mkdir(path, user=None):
    try:
        os.makedirs(str(path))
    except OSError as e:
        if e.errno == errno.EEXIST and path.is_dir():
            # exists already, fine.
            pass
        else:
            raise

    if user is not None:
        pw = pwd.getpwnam(user)
        os.chown(str(path), pw.pw_uid, pw.pw_gid)


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
    maxtime = max(f.stat().st_mtime for f in files)
    return datetime.datetime.fromtimestamp(maxtime)


# https://stackoverflow.com/a/29692864/7938656
# Wrap a function to restart itself automatically (used for threads that may crash)
def auto_restart(func):
    def wrapper(*args, **kwargs):
        delay = 0.001
        while True:
            try:
                func(*args, **kwargs)
            except BaseException as e:
                print('Exception in {}: {!r}\nRestarting.'.format(func.__name__, e))
            else:
                print('{} exited normally.\nRestarting.'.format(func.__name__))
            # exponential backoff
            print('Waiting {} seconds before restart.'.format(delay))
            time.sleep(delay)
            delay *= 2
    return wrapper
