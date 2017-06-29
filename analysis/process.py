import itertools
import math
from configparser import ConfigParser
import numpy as np
import pandas

from utils import Phase  # noqa

_entry_wait = 2  # min seconds between counted entries to top
_freeze_min_time = 2  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.05  # maximum speed to still consider a "freeze"
_freeze_window_size = 20  # number of samples for which the speed can't go above the max


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
    def __init__(self, trackfile, just_raw_data=False):
        self.trackfile = trackfile
        self.setupfile = trackfile.replace("-track.csv", "-setup.txt")

        self._read_trackfile()
        if not just_raw_data:
            self._generate_columns()
        self._read_setupfile()

    def _read_trackfile(self):
        colnames = ['time', 'status', 'x', 'y', 'numpts', '_1', '_2']
        self.df = pandas.read_csv(self.trackfile, header=None, names=colnames, index_col=0)

    def _generate_columns(self):
        ''' Calculate several auxiliary columns from the raw data
            read from CSV by _read_trackfile().
        '''
        # shorthand
        df = self.df

        # calculate derivatives and other derived values
        df['dx'] = df.x.diff()
        df['dy'] = df.y.diff()
        df['dt'] = df.index.to_series().diff()

        if df.dt.min() < 0:
            time_travel_indices = np.where(df.dt < 0)[0]
            print("\n[31mWARNING:[m Time travel detected!\n[31mNegative time deltas in following indices:[m " +
                  " ".join(str(x) for x in time_travel_indices) +
                  "\n"
                  )

        df['dist'] = np.linalg.norm(df[['dx','dy']], axis=1)
        df['speed'] = df.dist / df.dt
        df['theta'] = np.arctan2(df.dy, df.dx)  # reversed params are correct for numpy.arctan2

        # produce boolean arrays
        df['lost'] = (df.status == 'lost') | (df.status == 'init')
        df['missing'] = (df.status == 'missing')
        df['sketchy'] = (df.numpts > 1)
        # valid if this index *and* previous are both not 'lost' or 'missing'
        # need *both* as many columns are diffs relying on previous value
        df['valid'] = ~df.lost & ~df.missing & ~np.roll(df.lost, 1) & ~np.roll(df.missing, 1)

        df['frozen'] = df.valid & (df.speed.rolling(window=_freeze_window_size, center=True).max() < _freeze_max_speed)

    def _read_setupfile(self):
        self.config = ConfigParser()
        self.config.read(self.setupfile)
        # parse phases_data
        if 'phases' in self.config and 'phases_data' in self.config['phases']:
            phases_data_str = self.config['phases']['phases_data']
            self.phase_list = eval(phases_data_str)  # uses Phase namedtuple imported from utils
        else:
            self.phase_list = None

    def num_phases(self):
        return len(self.phase_list)

    def phase_starts(self):
        return list(itertools.accumulate([0] + [phase.length for phase in self.phase_list]))

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
        # Take second-to-last index so if just *one* sample in the new minute
        # (e.g. time=3600.0456), it still just counts as 60 minutes
        return int(math.ceil(self.df.index[-2] / 60.0))

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
        # shorthand
        df = self.df

        if minutes is 'all':
            selected = df.valid
        else:
            selected = df.valid & (df.index >= minutes[0]*60) & (df.index < minutes[1]*60)

        valid_count = df.valid.sum()

        dist_total = df.dist[selected].sum()
        time_total = df.dt[selected].sum()

        frozen_starts, frozen_lens = groups_where(df.frozen & selected)
        freeze_count, freeze_time, _ = self._sum_runs(frozen_starts, frozen_lens, min_runlength=_freeze_min_time)

        stats = {}

        if minutes is 'all':
            stats["#Datapoints"] = len(df)
            stats["#Valid"] = valid_count
            stats["%Valid datapoints"] = valid_count / float(len(df))
            stats["Total time (sec)"] = df.index.max()
            stats["Valid time (sec)"] = time_total

        if selected.any():  # no stats if no data, and avoids "nan" results, as well
            stats["Total distance traveled (?)"] = dist_total
            # TODO: weight averages by dt of each frame?
            stats["Avg. x coordinate"] = df.x[selected].mean()
            stats["Avg. y coordinate"] = df.y[selected].mean()
            stats["Avg. speed (?/sec)"] = dist_total / time_total
            stats["Avg. x speed (?/sec)"] = df.dx[selected].abs().sum() / time_total
            stats["Avg. y speed (?/sec)"] = df.dy[selected].abs().sum() / time_total
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
        df = self.df

        times = (df.index[starts+lens] - df.index[starts]).to_series()
        cumdist_vals = df.dist.cumsum().values
        dists = cumdist_vals[starts+lens] - cumdist_vals[starts]
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
