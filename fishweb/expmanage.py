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


def get_image(width=2592):
    height = int(width / 4 * 3)  # maintain 4:3 aspect ratio

    wiring.IR_on()

    tmpdir = tempfile.mkdtemp()
    fifoname = os.path.join(tmpdir, 'imgfifo')
    os.mkfifo(fifoname)

    cmdargs = ['raspistill',
               '--timeout', '1000000000',  # run effectively forever (until killed)
               '--timelapse', '5000',      # capture another image every 5 seconds
               '--width', str(width),
               '--height', str(height),
               '-awb', 'off',
               '-ex', 'off',
               '-ss', '200000',
               '-e', 'jpg',
               '-o', fifoname
               ]
    proc = subprocess.Popen(cmdargs)

    try:
        with open(fifoname, 'rb') as fifo:
            while True:
                data = fifo.read(10000)
                if data == '':
                    break
                yield data
    finally:
        # handle GeneratorExit caused by close() on the generator iterator,
        # as well as other possible exceptions
        proc.kill()
        os.remove(fifoname)
        os.rmdir(tmpdir)
        wiring.IR_off()


def start_experiment(expname, timelimit, startfromtrig, stimulus, inifile):
    if (not wiring.wiring_mocked) and (os.geteuid() != 0):
        cmdparts = ['sudo']  # fishbox.py must be run as root!
    else:
        cmdparts = []
    cmdparts.append(config.EXPSCRIPT)
    cmdparts.append("-t %d" % timelimit)
    if startfromtrig:
        cmdparts.append("--time-from-trigger")
    if stimulus == "nostim":
        cmdparts.append("--nostim")
    elif stimulus == "randstim":
        cmdparts.append("--randstim")
    cmdparts.append("--inifile %s" % inifile)
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
