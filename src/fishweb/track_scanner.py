import collections
import configparser
import dateutil
import os
import re
import time

from sqlalchemy import sql

import config
import utils
from utils import Phase  # noqa
import fishweb.db_schema as db_schema


_trackfile_parse_regexp = re.compile(r"(\d{8}-\d{4,6})-?(.*)-track.csv")


def _track_files_set():
    return set(config.TRACKDIR.glob("**/*-track.csv"))


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
            if int(numpts) > 1:
                state = "sketchy"
            states[state] += 1
            try:
                x = float(x)
                y = float(y)

                # place this sample in a heatmap bucket
                bucket_x = int(x * xbuckets)
                bucket_y = int(y * ybuckets)
                if state in ('acquired', 'sketchy'):
                    heatmap[(bucket_x, bucket_y)] += 1
                if state in ('missing', 'lost'):
                    invalid_heatmap[(bucket_x, bucket_y)] += 1
            except ValueError:
                pass  # not super important if we can't parse x,y

            # convert init to lost just for count (not for heatmaps)
            if state == "init":
                state = "lost"

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


def _get_setup_info(setupfile):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(setupfile)
        notes = parser.get('general', 'notes', fallback=None)
        trigger = parser.get('experiment', 'trigger', fallback=None)
        controller = parser.get('experiment', 'controller', fallback=None)
        stimulus = parser.get('experiment', 'stimulus', fallback=None)
        phase_data_str = parser.get('phases', 'phases_data', fallback=None)
        try:
            phase_data = eval(phase_data_str)  # uses Phase namedtuple imported from utils
        except TypeError:
            # old setupfile w/o matching phase tuple
            phase_data = []
        did_stim = any(phase.dostim for phase in phase_data)  # did any phases activate the conditional stimulus
        return notes, trigger, controller, stimulus, did_stim, phase_data
    except configparser.NoSectionError as e:
        print("configparser error: {}\nFile: {}".format(e, setupfile))
        raise


def _get_track_db_info(key, trackfile, trackrel):
    lines, asml, heat, invalid_heat = _get_track_data(trackfile)
    subdir, filename = os.path.split(trackrel)
    if subdir == '':
        # locally-created, most likely
        subdir = utils.get_boxname()
    starttime_str, exp_name = _trackfile_parse_regexp.search(filename).groups()
    starttime = dateutil.parser.parse(starttime_str)

    setupfile = trackfile.with_name(trackfile.name.replace('-track.csv', '-setup.txt'))
    if setupfile.is_file():
        notes, trigger, controller, stimulus, did_stim, phase_data = _get_setup_info(setupfile)
    else:
        setupfile = None
        notes = trigger = controller = stimulus = did_stim = phase_data = None

    new_row = dict(
        key=key,
        trackpath=trackfile,
        trackrel=trackrel,
        setupfile=setupfile,
        trigger=trigger,
        controller=controller,
        stimulus=stimulus,
        did_stim=did_stim,
        box=subdir,
        starttime=starttime,
        exp_name=exp_name,
        notes=notes,
        lines=lines,
        acquired=asml[0],
        sketchy=asml[1],
        missing=asml[2],
        lost=asml[3],
        heat=heat,
        invalid_heat=invalid_heat
    )

    return new_row, phase_data


def _store_phases(conn, key, phase_data):
    phases = db_schema.phases
    for phase in phase_data:
        insert = phases.insert().values(
            track_key=key,
            phase_num=phase.phasenum,
            phase_len=phase.length,
            stim_actual=phase.dostim,
        )
        conn.execute(insert)


def _update_track_data(conn):
    ''' Load all track data for present track files not currently in the database. '''
    # First, load all track data from db into a dictionary
    # to avoid thousands of individual database queries.
    tracks = db_schema.tracks
    select = sql.select([tracks.c.key])
    rows = conn.execute(select)
    # Make a set for fast existence checks
    tracks_in_db = set(row['key'] for row in rows)

    # Get a set of the tracks in the filesystem
    tracks_in_fs = _track_files_set()

    # Insert new tracks
    tracks_in_db = _add_new_tracks(conn, tracks_in_db, tracks_in_fs)
    # Delete removed tracks
    _clean_removed_tracks(conn, tracks_in_db, tracks_in_fs)


def _add_new_tracks(conn, tracks_in_db, tracks_in_fs):
    ''' For any track in the filesystem that isn't yet in the database,
        read and add it to the tracks and phases tables.

        Returns: set of tracks in the database after all additions.
    '''
    tracks = db_schema.tracks
    # Go through all track files, loading track data from DB if present
    # or computing and storing in DB if not yet.
    for trackfile in tracks_in_fs:
        mtime = os.stat(trackfile).st_mtime
        trackrel = os.path.relpath(trackfile, config.TRACKDIR)  # path relative to main tracks directory
        key = "%f|%s" % (mtime, trackrel)
        if key not in tracks_in_db:
            new_row, phase_data = _get_track_db_info(key, trackfile, trackrel)
            insert = tracks.insert().values(new_row)
            conn.execute(insert)
            if phase_data is not None:
                _store_phases(conn, key, phase_data)

            tracks_in_db.add(key)

    return tracks_in_db


def _clean_removed_tracks(conn, tracks_in_db, tracks_in_fs):
    ''' For any files in the database not found in the filesystem,
        delete them from the tracks and phases tables.
    '''
    tracks = db_schema.tracks
    phases = db_schema.phases
    for track_key in tracks_in_db:
        trackrel = track_key.split('|')[1]
        trackfile = config.TRACKDIR / trackrel
        if trackfile not in tracks_in_fs:
            delete = tracks.delete().where(tracks.c.key == track_key)
            conn.execute(delete)
            delete = phases.delete().where(phases.c.track_key == track_key)
            conn.execute(delete)


def scan_tracks(db_engine):
    ''' Scans the tracks directory for new files, updating the database for any
        it finds, forever.

        Made to be run in its own thread.
    '''
    conn = db_engine.connect()
    while True:
        _update_track_data(conn)

        time.sleep(5)
