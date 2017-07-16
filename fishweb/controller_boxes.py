import os
import re
import time

from bottle import abort, post, redirect, request, response, route, jinja2_template as template
from wtforms import Form, FieldList, FormField, HiddenField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError
from sqlalchemy import sql

import config
from fishweb import db_schema


def _inis():
    return sorted(f for f in os.listdir(config.INIDIR) if f.endswith('.ini'))


def _bgimgs():
    bgimgs = os.listdir(config.IMGDIR)
    return sorted(bgimgs)


def _get_box_rpc(tgtbox, boxes_rpc):
    if tgtbox not in boxes_rpc:
        abort(400, "Box {} not registered.".format(tgtbox))
    if not boxes_rpc[tgtbox].connected:
        abort(400, "Box {} not currently connected.".format(tgtbox))
    # use the module via RPC
    return boxes_rpc[tgtbox]


def _get_box_data(tgtbox, db):
    boxes = db_schema.boxes
    select = sql.select([boxes]).where(boxes.c.name == tgtbox)
    row = db.execute(select).fetchone()
    if not row:
        abort(400, "Box {} not registered.".format(tgtbox))
    if not row['connected']:
        abort(400, "Box {} not currently connected.".format(tgtbox))
    return dict(row)


def _get_expdata(tgtbox, db, count):
    tracks = db_schema.tracks
    select = sql.select([tracks]) \
                .where(tracks.c.box == tgtbox) \
                .order_by(tracks.c.starttime.desc()) \
                .limit(count)
    rows = db.execute(select)

    # gather data for returned rows
    invalid = []
    sketchy = []
    i = 0
    for row in rows:
        if i == 0:
            last_name = row['exp_name']
            last_starttime = row['starttime']
        invalid.append(row['missing'] + row['lost'])
        sketchy.append(row['sketchy'])
        i += 1

    # update count if fewer than requested rows found
    count = min(count, i)

    # create dictionary of results
    ret = {}
    ret['count'] = count
    if count:
        ret['last_name'] = last_name
        ret['last_starttime'] = "{:%a, %Y-%m-%d, %I:%M%p}".format(last_starttime)
        ret['invalid'] = invalid
        ret['min_invalid'] = min(invalid)
        ret['avg_invalid'] = sum(invalid) / float(count)
        ret['max_invalid'] = max(invalid)
        ret['sketchy'] = sketchy
        ret['min_sketchy'] = min(sketchy)
        ret['avg_sketchy'] = sum(sketchy) / float(count)
        ret['max_sketchy'] = max(sketchy)

    return ret


@route('/boxes')
def get_boxes(db):
    boxes = db_schema.boxes
    select = sql.select([boxes])
    rows = db.execute(select)
    ret = {}
    for row in rows:
        box = row['name']
        rowdict = dict(row)
        rowdict['exp_data'] = _get_expdata(box, db, count=10)
        if row['connected']:
            rowdict['lock_data'] = get_lock_data(box, db)
        ret[box] = rowdict
    return ret


@route('/lock_data/<tgtbox>')
def get_lock_data(tgtbox, db):
    box = _get_box_data(tgtbox, db)
    return {
        'running': box['exp_running'],
        'pid': box['exp_pid'],
        'starttime': box['exp_starttime'],
        'runtime': box['exp_runtime'],
        'curtime': time.time()
    }


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
    inifile = SelectField(".ini File", choices=list(zip(_inis(), _inis())))
    phases = FieldList(FormField(ExperimentPhaseForm), min_entries=10, max_entries=10)


@route('/')
def index():
    return template('boxes')


@route('/new/<tgtbox>')
def new_experiment_box(tgtbox, db):
    box = _get_box_data(tgtbox, db)

    form = NewExperimentForm()
    # first element must be visible
    form.phases[0].enabled.data = True

    return template('new', dict(form=form, box=box))


@post('/sync/<tgtbox>')
def post_sync_data(tgtbox, boxes_rpc):
    box = _get_box_rpc(tgtbox, boxes_rpc)

    try:
        return box.sync_data()
    except Exception as e:
        # For this one, pass back the full error to the client.
        abort(500, str(e))


@route('/image/<tgtbox>')
@route('/image/<tgtbox>/<width:int>')
def get_image(tgtbox, boxes_rpc, width=648):
    box = _get_box_rpc(tgtbox, boxes_rpc)

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
            if len(imgdata) < 16:
                continue  # ignore dud frames
            yield b"\n".join([b"--fishboxframe", b"Content-Type: image/jpeg", b"", imgdata, b""])
    finally:
        box.stop_img_stream()


@post('/clear_experiment/<tgtbox>')
def post_clear_experiment(tgtbox, boxes_rpc):
    box = _get_box_rpc(tgtbox, boxes_rpc)

    box.kill_experiment()


@post('/new/<tgtbox>')
def post_new(tgtbox, boxes_rpc):
    box = _get_box_rpc(tgtbox, boxes_rpc)

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
