import errno
import os
import shlex
import signal
import subprocess
import tempfile
import time

import config

# crude detection of whether we're on a Pi / have to run fishbox as root.
try:
    import wiringpi2  # noqa - it's fine that we're importing and not using
    _wiringpi2_available = True
except ImportError:
    _wiringpi2_available = False


def lock_exists():
    return os.path.isfile(config.LOCKFILE)


def lock_data():
    if not lock_exists():
        return {}

    with open(config.LOCKFILE, 'r') as f:
        pid, starttime, runtime = (int(line) for line in f)
        return {'pid': pid,
                'starttimestr': time.strftime("%X", time.localtime(starttime)),
                'starttime': starttime,
                'runtime': runtime
                }


def get_image():
    temp = tempfile.NamedTemporaryFile(suffix=".jpg")
    cmdargs = ['raspistill', '-t', '1', '-awb', 'off', '-ex', 'off', '-ss', '100000', '-o', temp.name]
    subprocess.call(cmdargs)
    with open(temp.name, 'rb') as f:
        data = f.read()
    temp.close()
    return data


def start_experiment(expname, timelimit, startfromtrig, stimulus, inifile):
    if _wiringpi2_available and os.geteuid() != 0:
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
    # Signal a process, using sudo, if the process exists/is running.
    if pid_exists(pid):
        #os.kill(pid, signal)
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
