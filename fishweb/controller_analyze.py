import base64
import csv
import glob
import io
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

from bottle import get, post, redirect, request, response, jinja2_template as template  # noqa: E402

from analysis import heatmaps, process, plot  # noqa: E402
import config  # noqa: E402
import utils   # noqa: E402


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
            processor = process.TrackProcessor(track)
        except ValueError as e:
            # often 'wrong number of columns' due to truncated file from killed experiment
            return template('error', errormsg="Failed to parse %s.  Please check and correct the file, deselect it, or archive it." % track, exception=traceback.format_exc())

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
        response.headers['Content-Disposition'] = 'attachment; filename=fishystats.csv'
        return csvstring
    else:
        return template('stats', keys=all_keys, stats=stats)


def _do_analyze(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)

    # ensure directories exist for plot creation
    trackreldir = os.path.dirname(trackrel)
    utils.mkdir(os.path.join(config.PLOTDIR, trackreldir))

    # look for debug frames to create links in the trace plot
    trackname = os.path.basename(trackfile).replace('-track.csv', '')
    dbgframedir = os.path.join(config.DBGFRAMEDIR, trackreldir, trackname)
    dbgframes = glob.glob(dbgframedir + "/subframe*.png")

    processor = process.TrackProcessor(trackfile)
    plotter = plot.TrackPlotter(processor, dbgframes)
    plotter.plot_heatmap()
    plot.savefig(config.PLOTDIR + "%s.10.heat.png" % trackrel)
    plotter.plot_invalidheatmap()
    plot.savefig(config.PLOTDIR + "%s.12.heat.invalid.png" % trackrel)
    if processor.num_phases() > 1:
        plotter.plot_heatmap(plot_type='per-phase')
        plot.savefig(config.PLOTDIR + "%s.14.heat.perphase.png" % trackrel)
    plotter.plot_heatmap(plot_type='per-minute')
    plot.savefig(config.PLOTDIR + "%s.15.heat.perminute.png" % trackrel)
    plotter.plot_trace()
    plot.savefig(config.PLOTDIR + "%s.20.plot.svg" % trackrel)
    #plotter.plot_x_fft()
    #plot.savefig(config.PLOTDIR + "%s.50.x_fft.png" % trackrel)
    #plotter.plot_x_fft(10)
    #plot.savefig(config.PLOTDIR + "%s.51.x_fft.10.png" % trackrel)
    #plotter.plot_leftright()
    #plot.savefig(config.PLOTDIR + "%s.52.leftright.png" % trackrel)


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
            pass  # nothing to be done here; we're processing in the background


@post('/analyze_selection/')
def post_analyze_selection():
    tracks = request.query.tracks.split('|')
    p = multiprocessing.Process(target=_analyze_selection, args=(tracks,))
    p.start()


@get('/heatmaps/')
def get_heatmaps():
    tracks = request.query.tracks.split('|')
    processors = [
        process.TrackProcessor(track, just_raw_data=True)
        for track in tracks
    ]
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
