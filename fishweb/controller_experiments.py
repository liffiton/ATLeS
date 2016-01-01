import glob
import platform
import re
from bottle import post, redirect, request, response, route, template, HTTPError
from wtforms import Form, BooleanField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError

import config
from fishweb import expmanage


def _inis():
    return sorted(glob.glob(config.INIDIR + "*.ini"))


class ManagerError(Exception):
    pass


def _get_box(tgtbox, boxes):
    local = request.app.config['fishweb.local']

    if local:
        assert tgtbox == platform.node()
        assert boxes is None
        # use the module directly
        return expmanage
    else:
        # use the module via RPC
        if tgtbox not in boxes:
            raise ManagerError("Box %s not registered." % tgtbox)
        if boxes[tgtbox].status != "connected":
            raise ManagerError("Box %s not connected." % tgtbox)

        return boxes[tgtbox]


@route('/lock_data/')
@route('/lock_data/<tgtbox>')
def get_lock_data(tgtbox=None, boxes=None):
    try:
        box = _get_box(tgtbox, boxes)
    except ManagerError as e:
        # invalid box - report it as a 404
        raise HTTPError(status=404, body=e.message)

    # RPyC doesn't return a real dict, and JSON won't serialize it,
    # so we make it a real dict.
    return dict(box.lock_data())


def _name_is_sane(form, field):
    if re.search('\W', field.data):
        raise ValidationError("Experiment name must be alphanumeric characters only.")


class NewExperimentForm(Form):
    ''' Form for creating a new experiment. '''
    expname = StringField("Experiment Name", [validators.Length(max=32), _name_is_sane])
    timelimit = IntegerField("Time Limit", [validators.NumberRange(min=1, max=24*60)])
    startfromtrig = BooleanField("startFromTrigger")
    stimulus = RadioField("Stimulus", choices=[('nostim', 'Off'), ('stim', 'On'), ('randstim', 'Randomized (equal chance off or on)')])
    inifile = SelectField(".ini File", choices=zip(_inis(), _inis()))


@route('/')
def index(boxes=None):
    local = request.app.config['fishweb.local']
    if local:
        # no need to choose a box, just give them the new exp. form
        return new_experiment_box(tgtbox=platform.node(), boxes=boxes)

    return template('boxes', dict(boxes=boxes, name='boxes'))


@route('/new/<tgtbox>')
def new_experiment_box(tgtbox, boxes=None):
    try:
        box = _get_box(tgtbox, boxes)
    except ManagerError:
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    form = NewExperimentForm()
    return template('new', dict(form=form, lock_exists=box.lock_exists(), box=tgtbox))


@post('/sync/<tgtbox>')
def post_sync_data(tgtbox=None, boxes=None):
    try:
        box = _get_box(tgtbox, boxes)
    except ManagerError:
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    return box.sync_data()


@route('/image/<tgtbox>')
def get_image(tgtbox=None, boxes=None):
    try:
        box = _get_box(tgtbox, boxes)
    except ManagerError:
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    imgdata = box.get_image()
    response.set_header('Content-type', 'image/jpeg')
    return imgdata


@post('/clear_experiment/')
@post('/clear_experiment/<tgtbox>')
def post_clear_experiment(tgtbox=None, boxes=None):
    try:
        box = _get_box(tgtbox, boxes)
    except ManagerError:
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    box.kill_experiment()


@post('/new/<tgtbox>')
def post_new(tgtbox=None, boxes=None):
    try:
        box = _get_box(tgtbox, boxes)
    except ManagerError:
        return template('error', errormsg="The specified box (%s) is not a valid choice.  Please go back and choose another." % tgtbox)

    if box.lock_exists():
        return template('error', errormsg="It looks like an experiment is already running on this box.  Please wait for it to finish before starting another.")

    # validate form data
    form = NewExperimentForm(request.forms)
    if not form.validate():
        return template('new', form=form, lock_exists=box.lock_exists(), box=tgtbox)

    expname = request.forms.expname
    timelimit = int(request.forms.timelimit)
    startfromtrig = bool(request.forms.startfromtrig)
    stimulus = request.forms.stimulus
    inifile = request.forms.inifile

    box.start_experiment(expname, timelimit, startfromtrig, stimulus, inifile)

    redirect("/")
