import csv
import multiprocessing
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Import matplotlib ourselves and make it use agg (not any GUI anything)
# before the analyze module pulls it in.
import matplotlib
matplotlib.use('Agg')
import analyze

from bottle import post, redirect, request, response, template

from fishweb import conf


@post('/stats/')
def post_stats():
    tracks = request.query.tracks.split('|')
    do_csv = request.query.csv
    stats = []
    all_keys = set()
    for track in tracks:
        curstats = {}
        curstats['Track file'] = track
        g = analyze.Grapher(track)
        curstats.update(g.read_setup(['experiment', 'at_runtime']))
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

    all_keys.remove('Track file')  # will be added as first column
    all_keys = sorted(list(all_keys))
    all_keys[:0] = ['Track file']  # prepend 'Track file' header

    if do_csv:
        output = StringIO()
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


def _do_analyze(trackname):
    name = trackname.split('/')[-1]
    g = analyze.Grapher(trackname)
    g.plot()
    g.savefig(conf.PLOTDIR + "%s.plot.png" % name)
    g.plot_heatmap()
    g.savefig(conf.PLOTDIR + "%s.heat.png" % name)
    g.plot_heatmap(10)
    g.savefig(conf.PLOTDIR + "%s.heat.10.png" % name)
    g.plot_leftright()
    g.savefig(conf.PLOTDIR + "%s.leftright.png" % name)


@post('/analyze/')
def post_analyze():
    trackname = request.query.path
    _do_analyze(trackname)
    redirect("/view/%s" % trackname)


def _analyze_selection(tracknames):
    for track in tracknames:
        _do_analyze(track)


@post('/analyze_selection/')
def post_analyze_selection():
    tracknames = request.query.selection.split('|')
    p = multiprocessing.Process(target=_analyze_selection, args=(tracknames,))
    p.start()


@post('/compare/')
def post_compare():
    track1 = request.query.p1
    track2 = request.query.p2
    g1 = analyze.Grapher(track1)
    g2 = analyze.Grapher(track2)
    g1.plot_leftright()
    g2.plot_leftright(addplot=True)
    name1 = track1.split('/')[-1]
    name2 = track2.split('/')[-1]
    # XXX: bit of a hack doing pyplot stuff outside of Grapher...
    matplotlib.pyplot.legend([name1 + " Left", name2 + " Left", name1 + " Right", name2 + " Right"], fontsize=8, loc=2)

    imgname = conf.PLOTDIR + "%s_%s_leftrights.png" % (name1, name2)
    g1.savefig(imgname)
    redirect("/" + imgname)
