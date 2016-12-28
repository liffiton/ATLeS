import csv
import multiprocessing
import os
import traceback
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Import matplotlib ourselves and make it use agg (not any GUI anything)
# before the analyze module pulls it in.
import matplotlib
matplotlib.use('Agg')
from . import analyze

from bottle import get, post, redirect, request, response, jinja2_template as template

import config
import utils


@get('/stats/')
def get_stats():
    tracks = request.query.tracks.split('|')
    do_csv = request.query.csv
    stats = []
    all_keys = set()
    for track in tracks:
        curstats = {}
        curstats['Track file'] = track

        try:
            g = analyze.Grapher(track)
        except ValueError as e:
            # often 'wrong number of columns' due to truncated file from killed experiment
            return template('error', errormsg="Failed to parse %s.  Please check and correct the file, deselect it, or archive it." % track, exception=traceback.format_exc())

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


def _do_analyze(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)

    # ensure directories exist for plot creation
    trackreldir = os.path.dirname(trackrel)
    utils.mkdir(os.path.join(config.PLOTDIR, trackreldir))

    g = analyze.Grapher(trackfile)
    g.plot()
    g.savefig(config.PLOTDIR + "%s.plot.png" % trackrel)
    g.plot_heatmap()
    g.savefig(config.PLOTDIR + "%s.heat.png" % trackrel)
    g.plot_heatmap(numplots='perminute')
    g.savefig(config.PLOTDIR + "%s.heat.perminute.png" % trackrel)
    g.plot_x_fft()
    g.savefig(config.PLOTDIR + "%s.x_fft.png" % trackrel)
    g.plot_x_fft(10)
    g.savefig(config.PLOTDIR + "%s.x_fft.10.png" % trackrel)
    g.plot_leftright()
    g.savefig(config.PLOTDIR + "%s.leftright.png" % trackrel)


@post('/analyze/')
def post_analyze():
    trackfile = request.query.path
    try:
        _do_analyze(trackfile)
    except ValueError as e:
        # often 'wrong number of columns' due to truncated file from killed experiment
        return template('error', errormsg="Failed to parse %s.  Please check and correct the file, deselect it, or archive it." % trackfile, exception=traceback.format_exc())
    redirect("/view/%s" % trackfile)


def _analyze_selection(trackfiles):
    for trackfile in trackfiles:
        try:
            _do_analyze(trackfile)
        except ValueError as e:
            # often 'wrong number of columns' due to truncated file from killed experiment
            return template('error', errormsg="Failed to parse %s.  Please check and correct the file, deselect it, or archive it." % trackfile, exception=traceback.format_exc())

@post('/analyze_selection/')
def post_analyze_selection():
    trackfiles = request.query.selection.split('|')
    p = multiprocessing.Process(target=_analyze_selection, args=(trackfiles,))
    p.start()


@post('/compare/')
def post_compare():
    track1 = request.query.p1
    track2 = request.query.p2
    g1 = analyze.Grapher(track1)
    g2 = analyze.Grapher(track2)
    g1.plot_leftright()
    g2.plot_leftright(addplot=True)
    # XXX: Note that this ignores directory names...
    # *May* inadvertently overwrite an existing plot if, e.g.,
    # We have box1/test-track.csv and box2/test-track.csv,
    # and both are just seen as "test-track.csv" here...
    name1 = os.path.basename(track1)
    name2 = os.path.basename(track2)
    # XXX: bit of a hack doing pyplot stuff outside of Grapher...
    matplotlib.pyplot.legend([name1 + " Left", name2 + " Left", name1 + " Right", name2 + " Right"], fontsize=8, loc=2)

    imgname = config.PLOTDIR + "%s_%s_leftrights.png" % (name1, name2)
    g1.savefig(imgname)
    redirect("/" + imgname)
