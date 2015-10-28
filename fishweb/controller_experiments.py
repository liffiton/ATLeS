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
    expname = StringField("Experiment Name", [validators.Length(max=32), _name_is_sane])
    timelimit = IntegerField("Time Limit", [validators.NumberRange(min=1, max=24*60)])
    startfromtrig = BooleanField("startFromTrigger")
    stimulus = RadioField("Stimulus", choices=[('nostim', 'Off'), ('stim', 'On'), ('randstim', 'Randomized (equal chance off or on)')])
    inifile = SelectField(".ini File", choices=zip(_inis(), _inis()))


@route('/new/')
def new_experiment(boxes=None):
    local = request.app.config['fishweb.local']
    if local:
        # no need to choose a box, just give them the new exp. form
        return new_experiment_box(tgtbox=platform.node(), boxes=boxes)

    #form.box.choices = [(box.name, box.name) for box in sorted(boxes.values())]
#    form.box.choices = [(box.name, box.name) for box in sorted(boxes.values())]
#
#    # add a dynamic validator for form.box based on the boxes list
#    def boxvalidator(form, field):
#        if field.data not in boxes or not boxes[field.data].up:
#            raise ValidationError("'%s' is not currently available.  Please choose another." % field.data)
#    form.box.validators.append(boxvalidator)
    return template('boxes', dict(boxes=boxes))


@route('/new/<tgtbox>')
def new_experiment_box(tgtbox, boxes=None):
    local = request.app.config['fishweb.local']
    if not local and (tgtbox not in boxes or not boxes[tgtbox].up):
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    form = CreateExperimentForm()
    return template('new', dict(form=form, lock_exists=expmanage.lock_exists(), hostname=tgtbox))


@post('/clear_experiment/')
def post_clear_experiment():
    expmanage.kill_experiment()


@post('/create/')
@post('/create/<tgtbox>')
def post_create(tgtbox=None, boxes=None):
    if expmanage.lock_exists():
        return template('error', errormsg="It looks like an experiment is already running on this box.  Please wait for it to finish before starting another.")

    local = request.app.config['fishweb.local']
    if not local and (tgtbox not in boxes or not boxes[tgtbox].up):
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    # validate form data
    form = CreateExperimentForm(request.forms)
    if not form.validate():
        return template('new', form=form, lock_exists=expmanage.lock_exists(), hostname=platform.node())

    expname = request.forms.expname
    timelimit = int(request.forms.timelimit)
    startfromtrig = bool(request.forms.startfromtrig)
    stimulus = request.forms.stimulus
    inifile = request.forms.inifile

    expmanage.start_experiment(expname, timelimit, startfromtrig, stimulus, inifile)

    redirect("/new/")
