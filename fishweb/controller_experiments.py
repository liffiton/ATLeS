import glob
import platform
import re
from bottle import post, redirect, request, route, template
from wtforms import Form, BooleanField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError

import config
from fishcontrol import expmanage


def _inis():
    return sorted(glob.glob(config.INIDIR + "*.ini"))


@route('/lock_data/')
def get_lock_data():
    if not expmanage.lock_exists():
        return None

    return expmanage.lock_data()


def _name_is_sane(form, field):
    if re.search('\W', field.data):
        raise ValidationError("Experiment name must be alphanumeric characters only.")


class CreateExperimentForm(Form):
    ''' Form for creating a new experiment. '''
    box = SelectField("Box", choices=[])
    expname = StringField("Experiment Name", [validators.Length(max=32), _name_is_sane])
    timelimit = IntegerField("Time Limit", [validators.NumberRange(min=1, max=24*60)])
    startfromtrig = BooleanField("startFromTrigger")
    stimulus = RadioField("Stimulus", choices=[('nostim', 'Off'), ('stim', 'On'), ('randstim', 'Randomized (equal chance off or on)')])
    inifile = SelectField(".ini File", choices=zip(_inis(), _inis()))


@route('/new/')
# @view('new')  # plugin keyword matching doesn't work if the @view decorator is applied
def new_experiment(boxes):
    form = CreateExperimentForm()
    form.box.choices = [(box.name, box.name) for box in sorted(boxes.values())]
    return template('new', dict(form=form, lock_exists=expmanage.lock_exists(), hostname=platform.node()))


@post('/clear_experiment/')
def post_clear_experiment():
    expmanage.kill_experiment()


@post('/create/')
def post_create(boxes):
    if expmanage.lock_exists():
        return template('error', errormsg="It looks like an experiment is already running on this box.  Please wait for it to finish before starting another.")

    # validate form data
    form = CreateExperimentForm(request.forms)
    form.box.choices = [(box.name, box.name) for box in sorted(boxes.values())]

    # add a dynamic validator for form.box based on the boxes list
    def boxvalidator(form, field):
        if field.data not in boxes or not boxes[field.data].up:
            raise ValidationError("'%s' is not currently available.  Please choose another." % field.data)
    form.box.validators.append(boxvalidator)

    if not form.validate():
        return template('new', form=form, lock_exists=expmanage.lock_exists(), hostname=platform.node())

    expname = request.forms.expname
    timelimit = int(request.forms.timelimit)
    startfromtrig = bool(request.forms.startfromtrig)
    stimulus = request.forms.stimulus
    inifile = request.forms.inifile

    expmanage.start_experiment(expname, timelimit, startfromtrig, stimulus, inifile)

    redirect("/new/")
