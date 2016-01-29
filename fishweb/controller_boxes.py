import glob
import platform
import re
import time

from bottle import abort, post, redirect, request, response, route, template
from wtforms import Form, BooleanField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError

import config
from fishweb import box_interface


def _inis():
    return sorted(glob.glob(config.INIDIR + "*.ini"))


def _get_box(tgtbox, boxes):
    local = request.app.config['fishweb.local']

    if local:
        assert tgtbox == platform.node()
        assert boxes is None
        # use the module directly
        return box_interface
    else:
        if tgtbox not in boxes:
            abort(400, "Box %s not registered." % tgtbox)
        if not boxes[tgtbox].connected:
            abort(400, "Box %s not currently connected." % tgtbox)
        # use the module via RPC
        return boxes[tgtbox]


@route('/boxes')
def get_boxes(boxes):
    return {name: box.as_dict() for name, box in boxes.items()}


@route('/lock_data/')
@route('/lock_data/<tgtbox>')
def get_lock_data(tgtbox=None, boxes=None):
    box = _get_box(tgtbox, boxes)

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
    box = _get_box(tgtbox, boxes)

    form = NewExperimentForm()
    return template('new', dict(form=form, lock_exists=box.lock_exists(), box=tgtbox))


@post('/sync/<tgtbox>')
def post_sync_data(tgtbox=None, boxes=None):
    box = _get_box(tgtbox, boxes)

    try:
        return box.sync_data()
    except Exception as e:
        # For this one, pass back the full error to the client.
        abort(500, str(e))


@route('/image/<tgtbox>')
@route('/image/<tgtbox>/<width:int>')
def get_image(tgtbox=None, width=648, boxes=None):
    box = _get_box(tgtbox, boxes)

    if box.lock_exists():
        return

    response.set_header('Content-type', 'multipart/x-mixed-replace; boundary=fishboxframe')
    try:
        box.start_img_stream(width)
        while True:
            if box.lock_exists():
                return
            time.sleep(0.5)
            imgdata = box.get_image()
            yield "--fishboxframe\nContent-Type: image/jpeg\n\n%s\n" % imgdata
    finally:
        box.stop_img_stream()


@post('/clear_experiment/')
@post('/clear_experiment/<tgtbox>')
def post_clear_experiment(tgtbox=None, boxes=None):
    box = _get_box(tgtbox, boxes)

    box.kill_experiment()


@post('/new/<tgtbox>')
def post_new(tgtbox=None, boxes=None):
    box = _get_box(tgtbox, boxes)

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
