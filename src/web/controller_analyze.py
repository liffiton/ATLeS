import base64
import csv
import io
import multiprocessing
import sys
from io import StringIO
from pathlib import Path

# Import matplotlib ourselves and make it use agg (not any GUI anything)
# before the analyze module pulls it in.
import matplotlib
matplotlib.use('Agg')

from bottle import get, post, redirect, request, response, jinja2_template as template  # noqa: E402

from analysis import heatmaps, process, plot  # noqa: E402
from .error_handlers import TrackParseError
import config  # noqa: E402
import utils   # noqa: E402


@get('/stats/')
def get_stats():
    trackrels = request.query.tracks.split('|')
    do_csv = request.query.csv
    stats = []
    all_keys = set()

    for trackrel in trackrels:
        curstats = {}
        curstats['Track file'] = trackrel

        try:
            processor = process.TrackProcessor(str(config.TRACKDIR / trackrel))
        except ValueError:
            # often 'wrong number of columns' due to truncated file from killed experiment
            raise(TrackParseError(trackrel, sys.exc_info()))

        curstats.update(processor.get_setup(['experiment', 'phases']))
        curstats.update(processor.get_stats(include_phases=True))
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
        response.headers['Content-Disposition'] = 'attachment; filename=atles_stats.csv'
        return csvstring
    else:
        return template('stats', keys=all_keys, stats=stats)


def _do_analyze(trackrel):
    trackrel = Path(trackrel)

    # ensure directories exist for plot creation
    trackreldir = trackrel.parent
    utils.mkdir(config.PLOTDIR / trackreldir)

    # look for debug frames to create links in the trace plot
    trackname = trackrel.name.replace('-track.csv', '')
    dbgframedir = config.DBGFRAMEDIR / trackreldir / trackname
    dbgframes = dbgframedir.glob("subframe*.png")

    processor = process.TrackProcessor(str(config.TRACKDIR / trackrel))
    plotter = plot.TrackPlotter(processor, dbgframes)
    plotter.plot_heatmap()

    def saveplot(filename):
        plot.savefig(str(config.PLOTDIR / filename))

    saveplot("{}.10.heat.png".format(trackrel))
    plotter.plot_invalidheatmap()
    saveplot("{}.12.heat.invalid.png".format(trackrel))
    if processor.num_phases() > 1:
        plotter.plot_heatmap(plot_type='per-phase')
        saveplot("{}.14.heat.perphase.png".format(trackrel))
    plotter.plot_heatmap(plot_type='per-minute')
    saveplot("{}.15.heat.perminute.png".format(trackrel))
    plotter.plot_trace()
    saveplot("{}.20.plot.svg".format(trackrel))


@post('/analyze/')
def post_analyze():
    trackrel = request.query.trackrel
    try:
        _do_analyze(trackrel)
    except ValueError:
        # often 'wrong number of columns' due to truncated file from killed experiment
        raise(TrackParseError(trackrel, sys.exc_info()))
    redirect("/view/{}".format(trackrel))


def _analyze_selection(trackrels):
    for trackrel in trackrels:
        try:
            _do_analyze(trackrel)
        except ValueError:
            # often 'wrong number of columns' due to truncated file from killed experiment
            pass  # nothing to be done here; we're processing in the background


@post('/analyze_selection/')
def post_analyze_selection():
    trackrels = request.query.trackrels.split('|')
    p = multiprocessing.Process(target=_analyze_selection, args=(trackrels,))
    p.start()


@get('/heatmaps/')
def get_heatmaps():
    trackrels = request.query.tracks.split('|')
    processors = []
    for trackrel in trackrels:
        try:
            processors.append(process.TrackProcessor(str(config.TRACKDIR / trackrel), just_raw_data=True))
        except ValueError:
            raise(TrackParseError(trackrel, sys.exc_info()))
    # verify all phases are equivalent
    # https://stackoverflow.com/a/3844832/7938656
    plengths = [[phase.length for phase in p.phase_list] for p in processors]
    if plengths.count(plengths[0]) != len(plengths):
        return template('error', errormsg="The provided tracks do not all have the same phase lengths.  Please select tracks that share an experimental setup.")

    # Save all images as binary to be included in the page directly
    # Base64-encoded.  (Saves having to write temporary data to filesystem.)
    images_data = []

    # use phases from the first track
    plengths = plengths[0]

    dataframes = [p.df for p in processors]
    phase_start = 0
    for i, length in enumerate(plengths):
        phase_end = phase_start + length
        x, y = heatmaps.get_timeslice(dataframes, phase_start*60, phase_end*60)
        title = "Phase {} ({}:00-{}:00)".format(i+1, phase_start, phase_end)
        ax = heatmaps.make_heatmap(x, y, title)
        plot.format_axis(ax)

        image_data = io.BytesIO()
        plot.savefig(image_data, format='png')
        images_data.append(
            base64.b64encode(image_data.getvalue()).decode()
        )

        phase_start = phase_end

    return template('view', imgdatas=images_data)
