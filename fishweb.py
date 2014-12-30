import csv
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


def _tracks():
    return sorted(glob.glob("logs/*-track.csv"))


def _imgs(name):
    return sorted(glob.glob("logs/img/%s*" % name))


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
def view(logname):
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
                if type(val) is np.float32 or type(val) is np.float64:
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
    try:
        os.makedirs("logs/img/")
    except:
        # exists already, fine.
        pass
    name = logname.split('/')[-1]
    g = analyze.Grapher()
    g.load(logname)
    g.plot()
    g.savefig("logs/img/%s.plot.png" % name)
    g.plot_heatmap()
    g.savefig("logs/img/%s.heat.png" % name)
    g.plot_heatmap(10)
    g.savefig("logs/img/%s.heat.10.png" % name)
    g.plot_leftright()
    g.savefig("logs/img/%s.leftright.png" % name)


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

    imgname = "logs/img/%s_%s_leftrights.png" % (name1, name2)
    g1.savefig(imgname)
    redirect("/" + imgname)


@post('/archive/')
def post_archive():
    try:
        os.makedirs("logs/archive/")
    except:
        # exists already, fine.
        pass
    logname = request.query.path
    name = logname.split('/')[-1].split('-track')[0]
    allfiles = glob.glob("logs/%s*" % name)
    for f in allfiles:
        shutil.move(f, "logs/archive/")

    redirect("/")


@route('/logs/<filename:path>')
def static_logs(filename):
    if (filename.endswith('.csv')):
        return static_file(filename, root='logs/', mimetype='text/plain')
    else:
        return static_file(filename, root='logs/')


if __name__ == '__main__':
    daemon = False
    testing = False
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 == "--daemon":
            daemon = True
        else:
            testing = True

    host = 'localhost' if testing else '0.0.0.0'

    if daemon:
        import daemon
        logfile = os.path.join(
                os.getcwd(),
                "bottle.log"
                )
        log = open(logfile,"w+")
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
