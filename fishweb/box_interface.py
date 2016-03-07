import errno
import os
import shlex
import signal
import subprocess
import tempfile
import time

import config
from fishbox import wiring


def lock_exists():
    return os.path.isfile(config.LOCKFILE)


def lock_data():
    if not lock_exists():
        return {'running': False}

    with open(config.LOCKFILE, 'r') as f:
        pid, starttime, runtime = (int(line) for line in f)
        return {'running': True,
                'pid': pid,
                'starttime': starttime,
                'runtime': runtime,
                'curtime': int(time.time())
                }


_raspistill = None
_imgfile = None


def start_img_stream(width=648):
    global _raspistill, _imgfile

    stop_img_stream()

    height = int(width / 4 * 3)  # maintain 4:3 aspect ratio
    #txtsize = max(16, int(height/20))

    _imgfile = tempfile.NamedTemporaryFile('rb')

    cmdargs = ['raspistill',
               '-t', '1000000000',   # run essentially forever
               '-tl', '500',         # take a photo every 500ms
               '-bm',                # use 'burst-mode' for constant capture
               '--width', str(width),
               '--height', str(height),
               '-awb', 'off',
               '--awbgains', '1,1,1',
               '-ex', 'off',
               '-ss', '100000',      # 100ms shutter
               '-br', '55',          # push up brightness a bit
               '-sa', '-100',        # completely desaturate
               '-e', 'jpg',
               '-th', '0:0:0',       # no thumbnail
               '-q', '15',           # high, but not crazy-high quality
               #'-a', '8',            # add a timestamp [doesn't update w/ -s or -tl]
               #'-ae', str(txtsize),  # with an appropriate font size
               '-o', _imgfile.name
               ]

    wiring.IR_on()
    _raspistill = subprocess.Popen(cmdargs)


def get_image():
    global _raspistill, _imgfile

    if _raspistill is None:
        return None

    with open(_imgfile.name, 'rb') as f:
        return f.read()


def stop_img_stream():
    global _raspistill, _imgfile
    if _raspistill is not None:
        _raspistill.terminate()
        _raspistill = None
        _imgfile.close()
    wiring.IR_off()


def start_experiment(expname, inifile, phases):
    '''
    Parameters:
       phases: Tuple(int, str) - length, stimulus
               stimulus choices: on, off, rand
    '''
    # check for raspistill and kill if running
    stop_img_stream()

    if (not wiring.wiring_mocked) and (os.geteuid() != 0):
        cmdparts = ['sudo']  # fishbox.py must be run as root!
    else:
        cmdparts = []

    cmdparts.append(config.EXPSCRIPT)
    cmdparts.append("--inifile %s" % inifile)
    # phases: each specified with a -p argument w/ ','-delimited values in each
    # e.g.: -p 10,off -p 30,rand -p 30,off
    for p in phases:
        cmdparts.append("--phases %s" % ','.join(str(x) for x in p))
    cmdparts.append(expname)
    cmdline = ' '.join(cmdparts)
    cmdargs = shlex.split(cmdline)

    subprocess.Popen(cmdargs)


# http://stackoverflow.com/a/6940314
def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def cond_sudo_kill(pid, signal):
    # Signal a process, using sudo if needed, if the process exists/is running.
    if pid_exists(pid):
        try:
            os.kill(pid, signal)
        except OSError:
            # Likely lacking permission due to process running as root,
            # so use sudo.
            subprocess.Popen(['sudo', 'kill', '-%d' % signal, '%d' % pid])


def kill_experiment():
    # kill process
    with open(config.LOCKFILE, 'r') as f:
        pid, starttime, runtime = (int(line) for line in f)

    print("Killing PID %d" % pid)
    cond_sudo_kill(pid, signal.SIGTERM)
    time.sleep(1.0)
    cond_sudo_kill(pid, signal.SIGTERM)
    time.sleep(1.0)
    cond_sudo_kill(pid, signal.SIGKILL)
    time.sleep(0.1)
    cond_sudo_kill(pid, signal.SIGKILL)
    time.sleep(0.1)

    assert not pid_exists(pid)

    # remove existing lockfile
    try:
        os.unlink(config.LOCKFILE)
    except:
        # might not exist anymore
        pass