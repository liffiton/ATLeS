import os
import shlex
import signal
import subprocess
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
    with open(config.LOCKFILE, 'r') as f:
        pid, starttime, runtime = (int(line) for line in f)
        return {'pid': pid,
                'starttimestr': time.strftime("%X", time.localtime(starttime)),
                'starttime': starttime,
                'runtime': runtime
                }


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


def kill_experiment():
    # kill process
    with open(config.LOCKFILE, 'r') as f:
        pid, starttime, runtime = (int(line) for line in f)
        print("Killing PID %d" % pid)
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1.0)
            os.kill(pid, signal.SIGTERM)
            time.sleep(1.0)
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.1)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            # at some point, we should get a "No such process error",
            # whether due to the process not existing in the first place,
            # or one of the signals succeeding
            pass
    # remove existing lockfile
    try:
        os.unlink(config.LOCKFILE)
    except:
        # might not exist anymore
        pass