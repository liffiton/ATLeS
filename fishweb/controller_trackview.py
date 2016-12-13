import collections
import fnmatch
import glob
import math
import os
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


def _dbgframes(trackrel):
    expname = trackrel[:trackrel.find("-track.csv")]
    return sorted(glob.glob(os.path.join(config.DBGFRAMEDIR, expname, "*")))


def _setupfile(trackpath):
    setupfile = trackpath[:trackpath.find("-track.csv")] + "-setup.txt"
    if os.path.isfile(setupfile):
        return setupfile
    else:
        return None


def _get_track_data(track):
    # configuration: # buckets for x/y in heatmap
    xbuckets = 30
    ybuckets = 15

    states = collections.Counter()
    heatmap = collections.Counter()
    velocities = []
    with open(track) as f:
        i = -1  # so lines = 0 if file is empty
        prev_x = None
        prev_y = None
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
                    x = float(x)
                    y = float(y)
                    if prev_x is not None:
                        dx = x - prev_x
                        dy = y - prev_y
                        # convert to [typically 3 digit] integer in range 0-1000
                        #velocities.append("%d" % (1000.0 * math.sqrt(dx*dx+dy*dy)))
                        velocities.append(math.sqrt(dx*dx+dy*dy))
                    else:
                        velocities.append(0)
                    prev_x = x
                    prev_y = y

                    # place this sample in a heatmap bucket
                    bucket_x = int(x * xbuckets)
                    bucket_y = int(y * ybuckets)
                    heatmap[(bucket_x, bucket_y)] += 1
                else:
                    velocities.append(0)
                    prev_x = None
                    prev_y = None
            except ValueError:
                pass  # not super important if we can't parse x,y
        lines = i+1
    if lines:
        aml = ["%0.3f" % (states[key] / float(lines)) for key in ('acquired', 'missing', 'lost')]
    else:
        aml = []
    if heatmap:
        maxheat = max(heatmap.values())
        # convert counts to 2-digit hex integer in range 0-255
        heatstr = '|'.join(''.join("%02x" % int(255 * float(heatmap[hx,hy])/maxheat) for hx in range(xbuckets)) for hy in range(ybuckets))
    else:
        heatstr = ""
    if velocities:
        veldata = [sum(velocities) / len(velocities), max(velocities)]
        veldata = ["%0.3f" % datum for datum in veldata]
    else:
        veldata = []

    return lines, aml, heatstr, veldata


# Cache computed a/m/l and heatmap data to avoid recomputation
track_data_cache = {}


@route('/tracks/')
@view('tracks')
def tracks():
    global track_data_cache
    local = request.app.config['fishweb.local']

    tracks = []
    for index, trackfile in enumerate(_tracks()):
        mtime = os.stat(trackfile).st_mtime
        trackrel = os.path.relpath(trackfile, config.TRACKDIR)
        key = "%f|%s" % (mtime, trackrel)
        if key in track_data_cache:
            lines, aml, heat, vel = track_data_cache[key]
        else:
            lines, aml, heat, vel = _get_track_data(trackfile)
            track_data_cache[key] = (lines, aml, heat, vel)
        tracks.append( (index, trackfile, trackrel, lines, aml, heat, vel, _imgs(trackrel), _dbgframes(trackrel), _setupfile(trackfile)) )
    return dict(tracks=tracks, local=local, name='tracks')


@route('/view/<trackfile:path>')
@view('view')
def view_track(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)
    return dict(imgs=_imgs(trackrel), trackfile=trackfile, trackrel=trackrel)


@route('/dbgframes/<trackfile:path>')
@view('view')
def debug_frames(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)
    return dict(imgs=_dbgframes(trackrel), trackfile=trackfile, trackrel=trackrel)


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
