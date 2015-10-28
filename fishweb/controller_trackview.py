import collections
import fnmatch
import glob
import math
import os
import platform
import tempfile
import zipfile

from bottle import post, request, response, route, static_file, view

import config


def _tracks():
    # match in all subdirs - thanks: http://stackoverflow.com/a/2186565
    tracks = []
    for root, dirnames, filenames in os.walk(config.TRACKDIR):
        for filename in fnmatch.filter(filenames, "*-track.csv"):
            tracks.append(os.path.join(root, filename))
    return sorted(tracks)


def _imgs(trackrel):
    return sorted(glob.glob(os.path.join(config.PLOTDIR, "%s*" % trackrel)))


def _get_track_data(track):
    states = collections.Counter()
    heatmap = collections.Counter()
    with open(track) as f:
        i = -1  # so lines = 0 if file is empty
        for i, line in enumerate(f):
            vals = line.split(',')
            try:
                state, x, y = vals[1:4]
            except ValueError:
                # most likely an empty line
                break
            if state == "init":
                state = "lost"
            states[state] += 1
            try:
                if state != "lost":
                    # convert to [typically 3 digit] integer in range 0-1000
                    x = "%d" % (1000.0 * (float(x) - math.fmod(float(x), 1.0/15)))
                    y = "%d" % (1000.0 * (float(y) - math.fmod(float(y), 1.0/10)))
                    heatmap[(x,y)] += 1
            except ValueError:
                pass  # not super important if we can't parse x,y
        lines = i+1
    if lines:
        aml = ["%0.3f" % (states[key] / float(lines)) for key in ('acquired', 'missing', 'lost')]
    else:
        aml = []
    if heatmap:
        maxheat = max(heatmap.values())
        heat = [(key[0], key[1], "%d" % (1000 * float(value)/maxheat)) for key, value in heatmap.items()]
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
    for index, trackfile in enumerate(_tracks()):
        mtime = os.stat(trackfile).st_mtime
        trackrel = os.path.relpath(trackfile, config.TRACKDIR)
        key = "%f|%s" % (mtime, trackrel)
        if key in track_data_cache:
            lines, aml, heat = track_data_cache[key]
        else:
            lines, aml, heat = _get_track_data(trackfile)
            track_data_cache[key] = (lines, aml, heat)
        tracks.append( (index, trackfile, trackrel, lines, aml, heat, _imgs(trackrel)) )
    return dict(tracks=tracks, box=platform.node())


@route('/view/<trackfile:path>')
@view('view')
def view_track(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)
    return dict(imgs=_imgs(trackrel), trackfile=trackfile, trackrel=trackrel)


@post('/download/')
def post_download():
    tracks = request.query.tracks.split('|')

    # write the archive into a temporary in-memory file-like object
    temp = tempfile.SpooledTemporaryFile()
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
        for track in tracks:
            archive.write(track)
    temp.seek(0)

    # force a download; give it a filename and mime type
    response.set_header('Content-Disposition', 'attachment; filename="tracks.zip"')
    response.set_header('Content-Type', 'application/zip')

    # relying on garbage collector to delete tempfile object
    # (and hence the file itself) when done sending
    return temp


@route('/data/<filename:path>')
def static_data(filename):
    if filename.endswith('.csv'):
        return static_file(filename, root=config.DATADIR, mimetype='text/plain')
    else:
        return static_file(filename, root=config.DATADIR)
