import math
from configparser import ConfigParser
import numpy as np

from utils import Phase  # noqa

_entry_wait = 2  # min seconds between counted entries to top
_freeze_min_time = 2  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.1  # maximum speed to still consider a "freeze"


def groups_where(vals):
    '''Return group start indices and lengths for all
    groups of consecutive true entries in vals.

    Adapted from: http://stackoverflow.com/q/4651683
    '''
    # where: convert vals from true/false to 1/0
    # TODO: necessary? likely removable / work-aroundable
    where = np.where(vals, 1, 0)
    # diffs: 1 if start of 1s, -1 if start of 0s, 0 otherwise
    diffs = np.concatenate( ([where[0]], np.diff(where)) )
    # change_idx: indexes of starts of runs plus index at end of list
    change_idx = np.concatenate( (np.where(diffs)[0], [len(where)-1]) )
    # starts: start of 1 runs
    starts = np.where(diffs > 0)[0]
    # lens: length of 1 runs (every other length is for a 1 run)
    lens = np.diff(change_idx)[::2]

    return starts, lens


class TrackProcessor(object):
    def __init__(self, trackfile):
        self.trackfile = trackfile
        self.setupfile = trackfile.replace("-track.csv", "-setup.txt")

        self._read_trackfile()
        self._read_setupfile()

    def _read_trackfile(self):
        def xy_to_float(s):
            if s != b'.':
                return float(s)
            else:
                return -1

        time, status, x, y, numpts = np.loadtxt(
            self.trackfile,
            delimiter=',',
            unpack=True,
            dtype={'names': ('time','status','x','y','numpts'), 'formats': ('f','S16','f','f','d')},
            converters={2: xy_to_float, 3: xy_to_float}
        )

        # calculate derivatives and other derived values
        #dx = np.gradient(x)
        #dy = np.gradient(y)
        #dt = np.gradient(time)
        dx = np.concatenate( ([0], np.diff(x)) )
        dy = np.concatenate( ([0], np.diff(y)) )
        dt = np.concatenate( ([0], np.diff(time)) )

        if np.min(dt) < 0:
            print("\n[31mWARNING:[m Time travel detected!\n[31mNegative time deltas in following indices:[m " +
                  " ".join(str(x) for x in np.where(dt < 0)) +
                  "\n"
                  )

        movement = np.matrix([dx,dy])
        try:
            self.dist = np.linalg.norm(movement, axis=0)
        except TypeError:
            # older version of numpy w/o axis argument
            self.dist = np.array(map(np.linalg.norm, np.transpose(movement)))
        self.speed = np.concatenate( ([0], self.dist[1:] / dt[1:]) )  # ignore invalid 0 entry in dt
        self.theta = np.arctan2(dy, dx)  # reversed params are correct for numpy.arctan2
        #self.dtheta = np.gradient(theta)
        #self.angular_velocity = dtheta / dt

        # produce boolean arrays
        self.valid = (status != b'lost') & (status != b'init') & (np.roll(status, 1) != b'lost') & (np.roll(status, 1) != b'init')  # valid if this index *and* previous are both not 'lost' or 'init'
        self.lost = (status == b'lost') | (status == b'init')
        self.missing = (status == b'missing')
        self.in_top = (y > 0.5)
        self.in_bottom = (y <= 0.5)
        self.in_left25 = (x < 0.25)
        self.in_right25 = (x > 0.75)
        self.frozen = (self.speed < _freeze_max_speed)

        # setup internal data
        self.len = len(time)
        self.time = time
        self.dt = dt
        self.x = x
        self.dx = dx
        self.y = y
        self.dy = dy
        self.numpts = numpts

    def _read_setupfile(self):
        self.config = ConfigParser()
        self.config.read(self.setupfile)
        # parse phases_data
        if 'phases' in self.config and 'phases_data' in self.config['phases']:
            phases_data_str = self.config['phases']['phases_data']
            self.phase_list = eval(phases_data_str)  # uses Phase namedtuple imported from utils
        else:
            self.phase_list = None

    def get_setup(self, sections):
        ret = {}
        ret['Setup file'] = self.setupfile

        for section in sections:
            if section not in self.config:
                continue

            for key in self.config[section]:
                ret[section + "__" + key] = self.config[section][key]

        return ret

    @property
    def len_minutes(self):
        return int(math.ceil(self.time[-1] / 60.0))

    def get_stats(self, include_phases=False):
        ret = {}
        ret.update(self._get_stats_time_range(minutes='all'))
        # only include per-phase stats if we have more than one phase
        if include_phases and self.phase_list is not None and len(self.phase_list) > 1:
            start_min = 0
            for phase in self.phase_list:
                phase_stats = self._get_stats_time_range(
                                minutes=(start_min, start_min+phase.length)
                              )
                ret.update(phase_stats)
                start_min += phase.length
        return ret

    def _get_stats_time_range(self, minutes=None):
        ''' Returns dictionary of statistics for the given time range.
            Params:
              minutes:  Tuple of (start_min, end_min) or 'all'.
                        If provided, analysis proceeds from start_min to
                        *beginning* of end_min.
                        If 'all', analysis covers entire dataset.
        '''
        if minutes is 'all':
            selected = self.valid
        else:
            selected = self.valid & (self.time >= minutes[0]*60) & (self.time < minutes[1]*60)

        valid_count = np.sum(selected)

        dist_total = np.sum(self.dist[selected])
        time_total = np.sum(self.dt[selected])

        frozen_starts, frozen_lens = groups_where(self.frozen & selected)
        freeze_count, freeze_time, _ = self._sum_runs(frozen_starts, frozen_lens, min_runlength=_freeze_min_time)

        left25_starts, left25_lens = groups_where(self.in_left25 & selected)
        left25_count, left25_time, left25_dist = self._sum_runs(left25_starts, left25_lens)

        right25_starts, right25_lens = groups_where(self.in_right25 & selected)
        right25_count, right25_time, right25_dist = self._sum_runs(right25_starts, right25_lens)

        top_starts, top_lens = groups_where(self.in_top & selected)
        top_count, top_time, top_dist = self._sum_runs(top_starts, top_lens)

        bottom_starts, bottom_lens = groups_where(self.in_bottom & selected)
        bottom_count, bottom_time, bottom_dist = self._sum_runs(bottom_starts, bottom_lens)

        # TODO:  cur_turn_time = 0
        # count erratic movements
        # "Erratic movement" = a string of at least _erratic_count 'turns' in less than _erratic_time seconds
        # "Turn" = abs(angular_velocity) > _turn_vel for at least _turn_time seconds
        # TODO

        stats = {}

        if minutes is 'all':
            stats["#Datapoints"] = len(self.valid)
            stats["#Valid"] = valid_count
            stats["%Valid datapoints"] = valid_count / float(len(self.valid))
            stats["Total time (sec)"] = self.time[-1]
            stats["Valid time (sec)"] = time_total

        if selected.any():  # no stats if no data, and avoids "nan" results, as well
            stats["Total distance traveled (?)"] = dist_total
            stats["Avg. x coordinate"] = np.mean(self.x[selected])
            stats["Avg. y coordinate"] = np.mean(self.y[selected])
            stats["Avg. speed (?/sec)"] = dist_total / time_total
            stats["Avg. x speed (?/sec)"] = np.sum(np.abs(self.dx[selected])) / time_total
            stats["Avg. y speed (?/sec)"] = np.sum(np.abs(self.dy[selected])) / time_total
            stats["#Entries to top"] = top_count
            stats["Time in top (sec)"] = top_time
            stats["Time in bottom (sec)"] = bottom_time
            stats["Distance in top (?)"] = top_dist
            stats["Distance in bottom (?)"] = bottom_dist
            if top_count:
                stats["Time of first top entry (sec)"] = self.time[top_starts[0]]
                stats["Avg. time per entry (sec)"] = top_time / top_count
                stats["Avg. distance per entry (?)"] = top_dist / top_count
            if bottom_time:
                stats["Top/bottom time ratio"] = top_time/bottom_time
            if bottom_dist:
                stats["Top/bottom distance ratio"] = top_dist/bottom_dist
            stats["#Freezes"] = freeze_count
            if freeze_count:
                stats["Total time frozen (sec)"] = freeze_time
                stats["Avg. time per freeze (sec)"] = freeze_time / freeze_count
                stats["Freeze frequency (per min)"] = 60.0*(freeze_count / time_total)

        if minutes is not 'all':
            stats = {
                "%s - minutes %04d-%04d" % (key, minutes[0], minutes[1]): value
                for key, value in stats.items()
            }

        return stats

    def _sum_runs(self, starts, lens, min_runlength=None, min_wait=None):
        times = self.time[starts+lens] - self.time[starts]
        cumdist = np.cumsum(self.dist)
        dists = cumdist[starts+lens] - cumdist[starts]
        if min_runlength is not None:
            which = times > min_runlength
        elif min_wait is not None:
            which = np.concatenate( ([True], np.diff(starts) > min_wait) )
        else:
            which = np.repeat([True], len(starts))
        count = which.sum()
        total_time = times[which].sum()
        total_dist = dists[which].sum()
        return count, total_time, total_dist
