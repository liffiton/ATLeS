import collections
import csv
import errno
import glob
import math
import multiprocessing
import os
import re
import shlex
import shutil
import subprocess
import sys
import StringIO

# 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
## Import gevent and monkey-patch before importing bottle.
#from gevent import monkey
#monkey.patch_all()

from bottle import post, redirect, request, response, route, run, static_file, view, template

from wtforms import Form, BooleanField, IntegerField, RadioField, SelectField, StringField, validators, ValidationError

# Import matplotlib ourselves and make it use agg (not any GUI anything)
# before the analyze module pulls it in.
import matplotlib
matplotlib.use('Agg')
import analyze

_LOGDIR = "logs/"
_LOCKFILE = _LOGDIR + "explockfile"
_INIDIR = "ini/"
_IMGDIR = _LOGDIR + "img/"
_ARCHIVEDIR = _LOGDIR + "archive/"
_EXPSCRIPT = "python fishbox.py"


def _tracks():
    return sorted(glob.glob(_LOGDIR + "*-track.csv"))


def _inis():
    return sorted(glob.glob(_INIDIR + "*.ini"))


def _lock_exists():
    return os.path.isfile(_LOCKFILE)


def _imgs(name):
    return sorted(glob.glob(_IMGDIR + "%s*" % name))


def _mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            # exists already, fine.
            pass
        else:
            raise


def _get_track_data(track):
    states = collections.Counter()
    heatmap = collections.Counter()
    with open(track) as f:
        i = -1  # so lines = 0 if file is empty
        for i, line in enumerate(f):
            vals = line.split(',')
            state, x, y = vals[1:4]
            if state == "init":
                state = "lost"
            states[state] += 1
            try:
                if state != "lost":
                    x = "%0.3f" % (float(x) - math.fmod(float(x), 1.0/15))
                    y = "%0.3f" % (float(y) - math.fmod(float(y), 1.0/10))
                    heatmap[(x,y)] += 1
            except ValueError:
                pass  # not super important if we can't parse x,y
        lines = i+1
    aml = ["%0.3f" % (states[key] / float(lines)) for key in 'acquired', 'missing', 'lost']
    if heatmap:
        maxheat = max(heatmap.values())
        heat = [(key[0], key[1], str(float(value)/maxheat)) for key, value in heatmap.items()]
    else:
        heat = []

    return lines, aml, heat


# Cache computed a/m/l and heatmap data to avoid recomputation
track_data_cache = {}


@route('/')
@view('index')
def index():
    global track_data_cache
    tracks = []
    for index, track in enumerate(_tracks()):
        if track in track_data_cache:
            lines, aml, heat = track_data_cache[track]
        else:
            lines, aml, heat = _get_track_data(track)
            track_data_cache[track] = (lines, aml, heat)
        name = track.split('/')[-1]
        tracks.append( (index, track, lines, aml, heat, _imgs(name)) )
    return dict(tracks=tracks)


@route('/new/')
def new_experiment():
    form = CreateExperimentForm()
    return template('new', form=form, lock_exists=_lock_exists())


@post('/delete_lockfile/')
def post_delete_lockfile():
    os.unlink(_LOCKFILE)


def _is_inifile(form, field):
    if field.data not in _inis():
        print str(field)
        raise ValidationError("Must specify an existing .ini file.")


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
        return template('new', form=form, lock_exists=_lock_exists())

    expname = request.forms.expname
    timelimit = int(request.forms.timelimit)
    startfromtrig = bool(request.forms.startfromtrig)
    stimulus = request.forms.stimulus
    inifile = request.forms.inifile

    if sys.platform in ['cygwin', 'nt']:
        cmdparts = []
    else:
        cmdparts = ['sudo']  # fishbox.py must be run as root!
    cmdparts.append(_EXPSCRIPT)
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

    redirect("/")


@route('/view/<logname:path>')
@view('view')
def view_log(logname):
    name = logname.split('/')[-1]
    return dict(imgs=_imgs(name), logname=logname)


@post('/stats/')
def post_stats():
    logs = request.query.logs.split('|')
    do_csv = request.query.csv
    stats = []
    all_keys = set()
    for log in logs:
        curstats = {}
        curstats['Log file'] = log
        g = analyze.Grapher()
        g.load(log)
        curstats.update(g.get_stats())
        for i in range(g.len_minutes):
            curstats.update(g.get_stats(minute=i))
            all_keys.update(curstats.keys())
        stats.append(curstats)
    for i in range(len(stats)):
        stat = stats[i]
        for k in all_keys:
            import numpy as np
            if k in stat:
                val = stat[k]
                if isinstance(val, (np.float32, np.float64)):
                    stat[k] = "%0.3f" % val
            else:
                stat[k] = ""

    all_keys.remove('Log file')  # will be added as first column
    all_keys = sorted(list(all_keys))
    all_keys[:0] = ['Log file']  # prepend 'Log file' header

    if do_csv:
        output = StringIO.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_keys)
        writer.writeheader()
        for stat in stats:
            writer.writerow(stat)
        csvstring = output.getvalue()
        output.close()
        response.content_type = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=fishystats.csv'
        return csvstring
    else:
        return template('stats', keys=all_keys, stats=stats)


def _do_analyze(logname):
    name = logname.split('/')[-1]
    g = analyze.Grapher()
    g.load(logname)
    g.plot()
    g.savefig(_IMGDIR + "%s.plot.png" % name)
    g.plot_heatmap()
    g.savefig(_IMGDIR + "%s.heat.png" % name)
    g.plot_heatmap(10)
    g.savefig(_IMGDIR + "%s.heat.10.png" % name)
    g.plot_leftright()
    g.savefig(_IMGDIR + "%s.leftright.png" % name)


@post('/analyze/')
def post_analyze():
    logname = request.query.path
    _do_analyze(logname)
    redirect("/view/%s" % logname)


@post('/analyze_all/')
def post_analyze_all():
    def do_all():
        for track in _tracks():
            _do_analyze(track)
    p = multiprocessing.Process(target=do_all)
    p.start()
    redirect("/")


@post('/compare/')
def post_compare():
    log1 = request.query.p1
    log2 = request.query.p2
    g1 = analyze.Grapher()
    g2 = analyze.Grapher()
    g1.load(log1)
    g2.load(log2)
    g1.plot_leftright()
    g2.plot_leftright(addplot=True)
    name1 = log1.split('/')[-1]
    name2 = log2.split('/')[-1]
    # XXX: bit of a hack doing pyplot stuff outside of Grapher...
    matplotlib.pyplot.legend([name1 + " Left", name2 + " Left", name1 + " Right", name2 + " Right"], fontsize=8, loc=2)

    imgname = _IMGDIR + "%s_%s_leftrights.png" % (name1, name2)
    g1.savefig(imgname)
    redirect("/" + imgname)


@post('/archive/')
def post_archive():
    logname = request.query.path
    name = logname.split('/')[-1].split('-track')[0]
    assert(name != '')
    allfiles = glob.glob(_LOGDIR + "%s*" % name)
    for f in allfiles:
        shutil.move(f, _ARCHIVEDIR)


@post('/unarchive/')
def post_unarchive():
    logname = request.query.path
    name = logname.split('/')[-1].split('-track')[0]
    allfiles = glob.glob(_ARCHIVEDIR + "%s*" % name)
    for f in allfiles:
        shutil.move(f, _LOGDIR)


@route('/logs/<filename:path>')
def static_logs(filename):
    if filename.endswith('.csv'):
        return static_file(filename, root=_LOGDIR, mimetype='text/plain')
    else:
        return static_file(filename, root=_LOGDIR)


@route('/ini/<filename:path>')
def static_inis(filename):
    return static_file(filename, root=_INIDIR)


if __name__ == '__main__':
    daemonize = False
    testing = False
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 == "--daemon":
            daemonize = True
        else:
            testing = True

    host = 'localhost' if testing else '0.0.0.0'

    # Create needed directories if not already there
    _mkdir(_IMGDIR)
    _mkdir(_ARCHIVEDIR)

    if daemonize:
        import daemon
        print("Launching daemon in the background.")
        logfile = os.path.join(
            os.getcwd(),
            "bottle.log"
        )
        with open(logfile, 'w+') as log:
            context = daemon.DaemonContext(
                working_directory=os.getcwd(),
                stdout=log,
                stderr=log
            )
            with context:
                # 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
                #run(host=host, port=8080, server='gevent', debug=False, reloader=False)
                run(host=host, port=8080, debug=False, reloader=False)

    else:
        # 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
        #run(host=host, port=8080, server='gevent', debug=testing, reloader=True)
        run(host=host, port=8080, debug=testing, reloader=True)
