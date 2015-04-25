import csv
import errno
import glob
import multiprocessing
import os
import shutil
import sys
import StringIO

# 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
## Import gevent and monkey-patch before importing bottle.
#from gevent import monkey
#monkey.patch_all()

from bottle import post, redirect, request, response, route, run, static_file, view, template

# Import matplotlib ourselves and make it use agg (not any GUI anything)
# before the analyze module pulls it in.
import matplotlib
matplotlib.use('Agg')
import analyze

_LOGDIR = "logs/"
_IMGDIR = _LOGDIR + "img/"
_ARCHIVEDIR = _LOGDIR + "archive/"


def _tracks():
    return sorted(glob.glob(_LOGDIR + "*-track.csv"))


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


@route('/')
@view('index')
def index():
    tracks = []
    for track in _tracks():
        with open(track) as f:
            i = -1  # so lines = 0 if file is empty
            for i, _ in enumerate(f):
                pass
            lines = i+1
        name = track.split('/')[-1]
        tracks.append( (track, lines, _imgs(name)) )
    return dict(tracks=tracks)


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
        g = analyze.Grapher()
        g.load(log)
        curstats = g.get_stats()
        all_keys.update(curstats.keys())
        curstats['Log file'] = log
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
    allfiles = glob.glob(_LOGDIR + "%s*" % name)
    for f in allfiles:
        shutil.move(f, _ARCHIVEDIR)

    redirect("/")


@route('/logs/<filename:path>')
def static_logs(filename):
    if filename.endswith('.csv'):
        return static_file(filename, root=_LOGDIR, mimetype='text/plain')
    else:
        return static_file(filename, root=_LOGDIR)


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
        #run(host=host, port=8080, server='gevent', debug=testing, reloader=testing)
        run(host=host, port=8080, debug=testing, reloader=testing)
