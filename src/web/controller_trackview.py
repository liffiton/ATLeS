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


def _get_track_data(db, filters):
    ''' Load track data for present track files.
        Uses the database (for any data previously computed/stored).
        Applies filters before returning data.
    '''
    tracks = db_schema.tracks
    select = sql.select([tracks]).order_by(tracks.c.trackrel)
    rows = db.execute(select)

    track_data = [
        collections.OrderedDict(row)  # ordered so filters show up in web interface in same order as columns in db
        for row in rows
        if _filter_row(row, filters)  # filter data (not a great method; better to use db WHERE clauses...)
    ]

    # add extra data not stored in db
    for row in track_data:
        row['asml'] = [str(x) for x in (row[key] for key in ('acquired', 'sketchy', 'missing', 'lost'))]
        row['imgs'] = _imgs(row['trackrel'])
        row['dbgframes'] = _dbgframes(row['trackrel'])
        row['setupfile'] = _setupfile(row['trackrel'])

    return track_data


def _filter_row(row, filters):
    def filterfunc(row, filt):
        val = filters[filt]['val']
        if filt == "tracks":
            tracks_set = set(val.split('|'))
            return row['trackrel'] in tracks_set
        elif filt.endswith(" (min)"):
            filt = filt.replace(" (min)", "")
            val = float(val)
            return row[filt] >= val
        elif filt.endswith(" (max)"):
            filt = filt.replace(" (max)", "")
            val = float(val)
            return row[filt] <= val
        elif isinstance(row[filt], bool):
            # need to convert our string query values to bool for the comparison
            return row[filt] == bool(val)
        else:
            return row[filt] == val

    return all(filterfunc(row, filt) for filt in filters)


def _get_filters(rows, selected):
    ''' Return a list of potential filter tuples for the given data in rows.

        return tuple: (param name, type, values or stats)
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
        if name in ('key', 'trackpath', 'trackrel', 'asml', 'imgs', 'dbgframes', 'setupfile'):
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


@route('/tracks/')
def tracks(db):
    selected_filters = {}
    for filt in request.query.keys():
        val = request.query.get(filt)
        if val == '':
            # unspecified min/max numeric values, e.g.
            continue

        # figure out query string without this selection (for backing out in web interface)
        querystring_without = '&'.join("{}={}".format(key, val) for key, val in request.query.items() if key != filt)
        # store for showing in page
        selected_filters[filt] = {
            'val': val,
            'querystring_without': querystring_without
        }

    track_data = _get_track_data(db, selected_filters)

    # possible filter params/values for selected rows
    possible_filters = _get_filters(track_data, selected_filters) if track_data else []

    return template('tracks',
                    tracks=track_data,
                    filters=possible_filters,
                    selected=selected_filters,
                    query_string=request.query_string,
                    query=request.query
                    )


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
