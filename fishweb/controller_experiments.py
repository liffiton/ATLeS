import glob
import os
import platform
import re
import shlex
import signal
import subprocess
import time
from bottle import post, redirect, request, route, template
from wtforms import Form, BooleanField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError

import config

# crude detection of whether we're on a Pi / have to run fishbox as root.
try:
    import wiringpi2  # noqa - it's fine that we're importing and not using
    _wiringpi2_available = True
except ImportError:
    _wiringpi2_available = False


def _inis():
    return sorted(glob.glob(config.INIDIR + "*.ini"))


def _lock_exists():
    return os.path.isfile(config.LOCKFILE)


@route('/lock_data/')
def lock_data():
    if not _lock_exists():
        return None

    with open(config.LOCKFILE, 'r') as f:
        pid, starttime, runtime = (int(line) for line in f)
        return {'pid': pid,
                'starttimestr': time.strftime("%X", time.localtime(starttime)),
                'starttime': starttime,
                'runtime': runtime
                }


@route('/new/')
def new_experiment():
    form = CreateExperimentForm()
    return template('new', form=form, lock_exists=_lock_exists(), hostname=platform.node())


@post('/clear_experiment/')
def post_clear_experiment():
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


def _name_is_sane(form, field):
    if re.search('\W', field.data):
        raise ValidationError("Experiment name must be alphanumeric characters only.")


class CreateExperimentForm(Form):
    ''' Form for creating a new experiment. '''
    expname = StringField("Experiment Name", [validators.Length(max=32), _name_is_sane])
    timelimit = IntegerField("Time Limit", [validators.NumberRange(min=1, max=24*60)])
    startfromtrig = BooleanField("startFromTrigger")
    stimulus = RadioField("Stimulus", choices=[('nostim', 'Off'), ('stim', 'On'), ('randstim', 'Randomized (equal chance off or on)')])
    inifile = SelectField(".ini File", choices=zip(_inis(), _inis()))


@post('/create/')
def post_create():
    if _lock_exists():
        return template('error', errormsg="It looks like an experiment is already running on this box.  Please wait for it to finish before starting another.")

    # validate form data
    form = CreateExperimentForm(request.forms)
    if not form.validate():
        return template('new', form=form, lock_exists=_lock_exists(), hostname=platform.node())

    expname = request.forms.expname
    timelimit = int(request.forms.timelimit)
    startfromtrig = bool(request.forms.startfromtrig)
    stimulus = request.forms.stimulus
    inifile = request.forms.inifile

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

    redirect("/new/")
