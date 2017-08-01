import collections
import datetime
import numbers
import statistics
import tempfile
import zipfile

from bottle import request, response, route, jinja2_template as template
from sqlalchemy import sql

import config
import web.db_schema as db_schema


def _imgs(trackrel):
    return [p.relative_to(config.BASEDIR)
            for p in
            sorted(config.PLOTDIR.glob("{}*".format(trackrel)))
            ]


def _dbgframes(trackrel):
    expname = trackrel.replace("-track.csv", "")
    return [p.relative_to(config.BASEDIR)
            for p in
            sorted((config.DBGFRAMEDIR / expname).glob("*"))
            ]


def _setupfile(trackrel):
    setupfile = trackrel.replace("-track.csv", "-setup.txt")
    if (config.TRACKDIR / setupfile).is_file():
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
            (row, asml, _imgs(row['trackrel']), _dbgframes(row['trackrel']), _setupfile(row['trackrel']))
        )

    return track_data


@route('/tracks/')
def tracks(db):
    track_data = _get_all_track_data(db)
    return template('tracks', tracks=track_data)


def _get_filters(rows, selected):
    ''' Return a list of potential filter tuples for the given data in rows.
         tuple: (param name, type, values or stats)
         "type": 'string' or 'numeric'
         "values or stats": a list of tuples (val, count) for string values
                            or
                            a tuple of (min,med,max) for numeric values

        Tries to generate a filter for every column in rows.
        Excludes any already in selected.
        Excludes others based on suitability (see code).
    '''
    filters = []
    for name in rows[0].keys():
        # exclude never-filtered columsn
        if name in ('key', 'trackpath', 'trackrel', 'setupfile'):
            continue
        # exclude any already selected
        if name in selected \
                or name + " (min)" in selected \
                or name + " (max)" in selected:
            continue

        # get a sorted list of unique non-None, non-"" values
        values = set(row[name] for row in rows)
        values.discard(None)
        values.discard('')
        values = sorted(values)

        # values that are all the same don't make good filters
        if len(values) == 1:
            continue
        # values that are all datetimes are likely not useful either
        if all(isinstance(x, datetime.datetime) for x in values):
            continue
        # super long strings are likely not useful either
        if all(len(str(x)) > 100 for x in values):
            continue

        # looks good: include it
        if all(isinstance(x, bool) for x in values):
            counts = collections.Counter(row[name] for row in rows if row[name] in values)
            filt = (name, "boolean", sorted(counts.items()))
        elif all(isinstance(x, numbers.Number) for x in values):
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
            counts = collections.Counter(row[name] for row in rows if row[name] in values)
            filt = (name, "string", sorted(counts.items()))
        filters.append(filt)

    return filters


def _select_track_data(track_data, filt, val):
    if filt == "tracks":
        tracks_set = set(val.split('|'))
        return [t for t in track_data if t[0]['trackrel'] in tracks_set]
    if filt.endswith(" (min)"):
        filt = filt.replace(" (min)", "")
        val = float(val)
        return [t for t in track_data if t[0][filt] >= val]
    elif filt.endswith(" (max)"):
        filt = filt.replace(" (max)", "")
        val = float(val)
        return [t for t in track_data if t[0][filt] <= val]
    elif isinstance(track_data[0][0][filt], bool):
        # need to convert our string query values to bool for the comparison
        return [t for t in track_data if t[0][filt] == bool(val)]
    else:
        return [t for t in track_data if t[0][filt] == val]


@route('/tracks/filter/')
def tracks_filter(db):
    track_data = _get_all_track_data(db)

    selected = {}
    for filt in request.query.keys():
        val = request.query.get(filt)
        if val == '':
            # unspecified min/max numeric values, e.g.
            continue

        # hack filtering for now (better: use DB)
        track_data = _select_track_data(track_data, filt, val)

        # figure out query string without this selection (for backing out in web interface)
        querystring_without = '&'.join("{}={}".format(key, val) for key, val in request.query.items() if key != filt)
        # store for showing in page
        selected[filt] = { 'val': val, 'querystring_without': querystring_without }

    # possible filter params/values for selected rows
    rows = [t[0] for t in track_data]
    filters = _get_filters(rows, selected) if rows else []

    return template('tracks', tracks=track_data, filters=filters, selected=selected, query_string=request.query_string, query=request.query)


@route('/view/<trackrel:path>')
def view_track(trackrel):
    return template('view', imgs=_imgs(trackrel), trackrel=trackrel)


@route('/dbgframes/<trackrel:path>')
def debug_frames(trackrel):
    return template('view', imgs=_dbgframes(trackrel), trackrel=trackrel)


@route('/download/')
def download():
    trackrels = request.query.tracks.split('|')

    # write the archive into a temporary in-memory file-like object
    temp = tempfile.SpooledTemporaryFile()
    with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
        for trackrel in trackrels:
            base_wildcard = trackrel.replace("-track.csv", "*")
            paths = config.TRACKDIR.glob(base_wildcard)
            for path in paths:
                archive.write(str(path),
                              str(path.relative_to(config.TRACKDIR))
                              )

    temp.seek(0)

    # force a download; give it a filename and mime type
    response.set_header('Content-Disposition', 'attachment; filename="data.zip"')
    response.set_header('Content-Type', 'application/zip')

    # relying on garbage collector to delete tempfile object
    # (and hence the file itself) when done sending
    return temp
