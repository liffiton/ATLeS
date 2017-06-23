import os
import re
import time

from bottle import abort, post, redirect, request, response, route, jinja2_template as template
from wtforms import Form, FieldList, FormField, HiddenField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError

import config


def _inis():
    inifiles = [f for f in os.listdir(config.INIDIR) if f.endswith('.ini')]
    return sorted(inifiles)


def _bgimgs():
    bgimgs = os.listdir(config.IMGDIR)
    return sorted(bgimgs)


def _get_box(tgtbox, boxes):
    if tgtbox not in boxes:
        abort(400, "Box %s not registered." % tgtbox)
    if not boxes[tgtbox].connected:
        abort(400, "Box %s not currently connected." % tgtbox)
    # use the module via RPC
    return boxes[tgtbox]


@route('/boxes')
def get_boxes(boxes):
    return {name: box.as_dict() for name, box in boxes.items()}


@route('/lock_data/<tgtbox>')
def get_lock_data(tgtbox, boxes=None):
    box = _get_box(tgtbox, boxes)

    # RPyC doesn't return a real dict, and JSON won't serialize it,
    # so we make it a real dict.
    return dict(box.lock_data())


def _name_is_sane(form, field):
    if re.search('\W', field.data):
        raise ValidationError("Experiment name must be alphanumeric characters only.")


def _skip_if_not_enabled(form, field):
    if form.enabled.data != "True":
        # clear any previous errors
        field.errors[:] = []
        raise validators.StopValidation()


def _skip_if_no_display(form, field):
    if form.hasdisplay.data != "True":
        # clear any previous errors
        field.errors[:] = []
        raise validators.StopValidation()


class ExperimentPhaseForm(Form):
    enabled = HiddenField("enabled")
    hasdisplay = HiddenField("hasdisplay")  # will be filled by box information in template
    length = IntegerField("Length", [_skip_if_not_enabled, validators.InputRequired(), validators.NumberRange(min=1, max=7*24*60)])
    stimulus = RadioField("Stimulus", choices=[('off', 'Off'), ('on', 'On'), ('rand', 'Random choice')], validators=[_skip_if_not_enabled, validators.InputRequired()])
    imgoptions = [""] + _bgimgs()
    background = SelectField("Background Image", default="", choices=zip(imgoptions, imgoptions), validators=[_skip_if_not_enabled, _skip_if_no_display, validators.InputRequired()])


class NewExperimentForm(Form):
    ''' Form for creating a new experiment. '''
    expname = StringField("Experiment Name", [validators.Length(max=32), _name_is_sane])
    inifile = SelectField(".ini File", choices=zip(_inis(), _inis()))
    phases = FieldList(FormField(ExperimentPhaseForm), min_entries=10, max_entries=10)


@route('/')
def index(boxes=None):
    return template('boxes')


@route('/new/<tgtbox>')
def new_experiment_box(tgtbox, boxes=None):
    box = _get_box(tgtbox, boxes)

    form = NewExperimentForm()
    # first element must be visible
    form.phases[0].enabled.data = True

    return template('new', dict(form=form, box=box))


@post('/sync/<tgtbox>')
def post_sync_data(tgtbox, boxes=None):
    box = _get_box(tgtbox, boxes)

    try:
        return box.sync_data()
    except Exception as e:
        # For this one, pass back the full error to the client.
        abort(500, str(e))


@route('/image/<tgtbox>')
@route('/image/<tgtbox>/<width:int>')
def get_image(tgtbox, width=648, boxes=None):
    box = _get_box(tgtbox, boxes)

    if box.lock_exists():
        # must yield then return in a generator function
        yield template('error', errormsg="It looks like an experiment is currently running on this box.  Image capture only works while the box is idle.")
        return

    try:
        try:
            box.start_img_stream(width)
        except OSError as e:
            # must yield then return in a generator function
            yield template('error', errormsg="Failed to start image stream capture.", exception=e)
            return

        # all set; carry on
        response.set_header('Content-type', 'multipart/x-mixed-replace; boundary=fishboxframe')
        while True:
            if box.lock_exists():
                return
            time.sleep(0.5)
            imgdata = box.get_image()
            if imgdata is None:
                return
            yield "--fishboxframe\nContent-Type: image/jpeg\n\n%s\n" % imgdata
    finally:
        box.stop_img_stream()


@post('/clear_experiment/<tgtbox>')
def post_clear_experiment(tgtbox, boxes=None):
    box = _get_box(tgtbox, boxes)

    box.kill_experiment()


@post('/new/<tgtbox>')
def post_new(tgtbox, boxes=None):
    box = _get_box(tgtbox, boxes)

    if box.lock_exists():
        return template('error', errormsg="It looks like an experiment is already running on this box.  Please wait for it to finish before starting another.")

    # validate form data
    form = NewExperimentForm(request.forms)
    if not form.validate():
        return template('new', dict(form=form, box=box))

    expname = form.expname.data
    inifile = os.path.join(config.INIDIR, form.inifile.data)

    def get_phase(phase):
        length = phase.length.data
        stimulus = phase.stimulus.data
        background = phase.background.data
        return (length, stimulus, background)

    phases = [get_phase(p) for p in form.phases if p.enabled.data == 'True']

    box.start_experiment(expname, inifile, phases)

    redirect("/")
