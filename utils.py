import datetime
import errno
import glob
import os
import socket

from contextlib import closing

import plumbum


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
    files = glob.glob(os.path.join(dir, '*'))
    if not files:
        return
    maxtime = max(os.path.getmtime(f) for f in files)
    return datetime.datetime.fromtimestamp(maxtime)
