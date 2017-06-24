import collections
import fnmatch
import glob
import os
import tempfile
import zipfile

from bottle import post, request, response, route, static_file, jinja2_template as template
from sqlalchemy import sql

import config
import fishweb.db_schema as db_schema


def _track_files():
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
    # configuration: # buckets for x/y in heatmaps
    xbuckets = 30
    ybuckets = 15

    states = collections.Counter()
    heatmap = collections.Counter()
    invalid_heatmap = collections.Counter()
    with open(track) as f:
        lines = 0
        for line in f:
            vals = line.split(',')
            try:
                state, x, y = vals[1:4]
            except ValueError:
                # most likely an empty line
                break

            lines += 1
            if state == "init":
                state = "lost"
            states[state] += 1
            try:
                x = float(x)
                y = float(y)

                # place this sample in a heatmap bucket
                bucket_x = int(x * xbuckets)
                bucket_y = int(y * ybuckets)
                if state != "lost":
                    heatmap[(bucket_x, bucket_y)] += 1
                if state != "acquired":
                    invalid_heatmap[(bucket_x, bucket_y)] += 1
            except ValueError:
                pass  # not super important if we can't parse x,y

    if lines:
        aml = ["%0.3f" % (states[key] / float(lines)) for key in ('acquired', 'missing', 'lost')]
    else:
        aml = [0, 0, 0]

    def normalize_stringify(heatdata):
        maxheat = max(heatdata.values())
        # convert counts to 2-digit hex integer in range 0-255
        ret = '|'.join(''.join("%02x" % int(255 * float(heatdata[hx,hy])/maxheat) for hx in range(xbuckets)) for hy in range(ybuckets))
        return ret

    heatstr = normalize_stringify(heatmap) if heatmap else ""
    invalid_heatstr = normalize_stringify(invalid_heatmap) if invalid_heatmap else ""

    return lines, aml, heatstr, invalid_heatstr


def _get_all_track_data(db):
    ''' Load all track data for present track files.
        Uses the database (for any data previously computed/stored). '''
    # First, load all track data from db into a dictionary
    # to avoid thousands of individual database queries.
    tracks = db_schema.tracks
    select = sql.select([tracks])
    rows = db.execute(select)
    # Make a dictionary so it's indexable by key.
    track_db_data = {row['key']: row for row in rows}

    track_data = []

    # Go through all track files, loading track data from DB if present
    # or computing and storing in DB if not yet.
    for trackfile in _track_files():
        mtime = os.stat(trackfile).st_mtime
        trackrel = os.path.relpath(trackfile, config.TRACKDIR)
        key = "%f|%s" % (mtime, trackrel)
        if key in track_db_data:
            row = track_db_data[key]
        else:
            lines, aml, heat, invalid_heat = _get_track_data(trackfile)
            insert = tracks.insert().values(
                key=key,
                lines=lines,
                acquired=aml[0],
                missing=aml[1],
                lost=aml[2],
                heat=heat,
                invalid_heat=invalid_heat
            )
            db.execute(insert)
            select = sql.select([tracks]).where(tracks.c.key == key)
            row = db.execute(select).fetchone()

        track_data.append(
            (trackfile,
             trackrel,
             row['lines'],
             [str(row['acquired']), str(row['missing']), str(row['lost'])],
             row['heat'],
             row['invalid_heat'],
             _imgs(trackrel),
             _dbgframes(trackrel),
             _setupfile(trackfile)
             )
        )

    return track_data


@route('/tracks/')
def tracks(db):
    track_data = _get_all_track_data(db)
    return template('tracks', tracks=track_data)


@route('/view/<trackfile:path>')
def view_track(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)
    return template('view', imgs=_imgs(trackrel), trackfile=trackfile, trackrel=trackrel)


@route('/dbgframes/<trackfile:path>')
def debug_frames(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)
    return template('view', imgs=_dbgframes(trackrel), trackfile=trackfile, trackrel=trackrel)


@post('/download/')
def post_download():
    tracks = request.query.tracks.split('|')

    # write the archive into a temporary in-memory file-like object
    temp = tempfile.SpooledTemporaryFile()
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
        for trackpath in tracks:
            basename = trackpath.replace("-track.csv", "")
            paths = glob.glob(basename + "*")
            for path in paths:
                archive.write(path)

    temp.seek(0)

    # force a download; give it a filename and mime type
    response.set_header('Content-Disposition', 'attachment; filename="data.zip"')
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
