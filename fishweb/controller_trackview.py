import collections
import datetime
import fnmatch
import glob
import numbers
import os
import re
import statistics
import tempfile
import zipfile

from bottle import post, request, response, route, static_file, jinja2_template as template
from sqlalchemy import sql

import config
import fishweb.db_schema as db_schema


_trackfile_parse_regexp = re.compile(r"(\d{8}-\d{6})-(.*)-track.csv")


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
    expname = trackrel.replace("-track.csv", "")
    return sorted(glob.glob(os.path.join(config.DBGFRAMEDIR, expname, "*")))


def _setupfile(trackpath):
    setupfile = trackpath.replace("-track.csv", "-setup.txt")
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
    # TODO: use pandas to simplify parsing/analysis
    with open(track) as f:
        lines = 0
        for line in f:
            vals = line.split(',')
            try:
                state, x, y, numpts = vals[1:5]
            except ValueError:
                # most likely an empty line
                break

            lines += 1
            if state == "init":
                state = "lost"
            if int(numpts) > 1:
                state = "sketchy"
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
        asml = ["%0.3f" % (states[key] / float(lines)) for key in ('acquired', 'sketchy', 'missing', 'lost')]
    else:
        asml = [0, 0, 0, 0]

    def normalize_stringify(heatdata):
        maxheat = max(heatdata.values())
        # convert counts to 2-digit hex integer in range 0-255
        ret = '|'.join(''.join("%02x" % int(255 * float(heatdata[hx,hy])/maxheat) for hx in range(xbuckets)) for hy in range(ybuckets))
        return ret

    heatstr = normalize_stringify(heatmap) if heatmap else ""
    invalid_heatstr = normalize_stringify(invalid_heatmap) if invalid_heatmap else ""

    return lines, asml, heatstr, invalid_heatstr


def _get_all_track_data(db):
    ''' Load all track data for present track files.
        Uses the database (for any data previously computed/stored). '''
    tracks = db_schema.tracks
    select = sql.select([tracks]).order_by(tracks.c.trackrel)
    rows = db.execute(select)

    track_data = []

    for row in rows:
        asml = [str(x) for x in (row[key] for key in ('acquired', 'sketchy', 'missing', 'lost'))]
        track_data.append(
            (row, asml, _imgs(row['trackrel']), _dbgframes(row['trackrel']), _setupfile(row['trackpath']))
        )

    return track_data


@route('/tracks/')
def tracks(db):
    track_data = _get_all_track_data(db)
    return template('tracks', tracks=track_data)


def _get_filters(rows, selected):
    ''' Return a list of potential filter tuples for the given data in rows.
         tuple: (param name, list of values, stats)
         "value": (value, count of rows with that value)

        If values are all numeric, no list is given (signalled to template with
        string "numeric") and stats is filled in with statistics of the values
        to present to user.

        Tries to generate a filter for every column in rows.
        Excludes any already in selected.
        Excludes others based on suitability (see code).
    '''
    filters = []
    for name in rows[0].keys():
        # exclude any already selected
        if name in selected \
                or name + " (min)" in selected \
                or name + " (max)" in selected:
            continue

        values = sorted(list(set(row[name] for row in rows)))
        # values that are all unique or all same don't make good filters
        if len(values) == len(rows) or len(values) == 1:
            continue
        # values that are all datetimes are likely not useful either
        if all(isinstance(x, datetime.datetime) for x in values):
            continue
        # super long strings are likely not useful either
        if all(len(str(x)) > 100 for x in values):
            continue

        # looks good: include it
        if all(isinstance(x, numbers.Number) for x in values):
            # values that are all numeric will ask for min/max separately
            # signal with values="numeric"
            # get/include stats from values
            stats = (
                min(values),
                round(statistics.median(values), 3),
                max(values),
            )
            filt = (name, "numeric", stats)
        else:
            counts = [
                sum(1 for row in rows if row[name] == val)
                for val in values
            ]
            filt = (name, zip(values, counts), None)
        filters.append(filt)

    return filters


def _select_track_data(track_data, filt, val):
    if filt.endswith(" (min)"):
        filt = filt.replace(" (min)", "")
        val = float(val)
        return [t for t in track_data if t[0][filt] >= val]
    elif filt.endswith(" (max)"):
        filt = filt.replace(" (max)", "")
        val = float(val)
        return [t for t in track_data if t[0][filt] <= val]
    else:
        return [t for t in track_data if t[0][filt] == val]


@route('/tracks/filter/')
def tracks_filter(db):
    track_data = _get_all_track_data(db)

    query_tracks = request.query.get('tracks')
    if query_tracks is not None:
        tracks_set = set(query_tracks.split('|'))
        track_data = [t for t in track_data if t[0]['trackpath'] in tracks_set]

    # hack filtering for now (better: use DB)
    selected = {}
    for filt in request.query.keys():
        if filt == 'tracks':
            continue

        val = request.query.get(filt)
        if val == '':
            # unspecified min/max numeric values, e.g.
            continue

        track_data = _select_track_data(track_data, filt, val)
        # figure out query string without this selection (for backing out in web interface)
        querystring_without = '&'.join("{}={}".format(key, val) for key, val in request.query.items() if key != filt)
        # store for showing in page
        selected[filt] = { 'val': val, 'querystring_without': querystring_without }

    # possible filter params/values for selected rows
    rows = [t[0] for t in track_data]
    filters = _get_filters(rows, selected) if rows else []

    return template('tracks', tracks=track_data, filters=filters, selected=selected, query_string=request.query_string, query=request.query)


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
