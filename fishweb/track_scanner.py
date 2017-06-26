import collections
import dateutil
import fnmatch
import os
import platform
import re
import time

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


def _update_track_data(conn):
    ''' Load all track data for present track files not currently in the database. '''
    # First, load all track data from db into a dictionary
    # to avoid thousands of individual database queries.
    tracks = db_schema.tracks
    select = sql.select([tracks])
    rows = conn.execute(select)
    # Make a dictionary so it's indexable by key.
    track_db_data = {row['key']: row for row in rows}

    # Go through all track files, loading track data from DB if present
    # or computing and storing in DB if not yet.
    for trackfile in _track_files():
        mtime = os.stat(trackfile).st_mtime
        trackrel = os.path.relpath(trackfile, config.TRACKDIR)  # path relative to main tracks directory
        key = "%f|%s" % (mtime, trackrel)
        if key not in track_db_data:
            lines, asml, heat, invalid_heat = _get_track_data(trackfile)
            subdir, filename = os.path.split(trackrel)
            if subdir == '':
                # locally-created, most likely
                subdir = platform.node()
            starttime_str, exp_name = _trackfile_parse_regexp.search(filename).groups()
            starttime = dateutil.parser.parse(starttime_str)
            insert = tracks.insert().values(
                key=key,
                trackpath=trackfile,
                trackrel=trackrel,
                box=subdir,
                starttime=starttime,
                exp_name=exp_name,
                lines=lines,
                acquired=asml[0],
                sketchy=asml[1],
                missing=asml[2],
                lost=asml[3],
                heat=heat,
                invalid_heat=invalid_heat
            )
            conn.execute(insert)


def scan_tracks(db_engine):
    ''' Scans the tracks directory for new files, updating the database for any
        it finds, forever.

        Made to be run in its own thread.
    '''
    conn = db_engine.connect()
    while True:
        _update_track_data(conn)

        time.sleep(10)
