import configparser
import itertools
import math
import numpy as np
import pandas

from common import Phase  # noqa

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

        self._read_setupfile()

        self._read_trackfile()
        if not just_raw_data:
            self._generate_columns()

    def _read_trackfile(self):
        colnames = ['time', 'status', 'x', 'y', 'numpts', '_1', '_2']
        # for handling data w/ '.' in place of unknown initial locations

        def xy_to_float(s):
            if s == '.':
                return -1
            else:
                return float(s)

        self.df = pandas.read_csv(
            self.trackfile, header=None, names=colnames, index_col=0,
            converters={2: xy_to_float, 3: xy_to_float}
        )

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

        trigger_exp = self.config['experiment']['trigger']
        # create xpos/ypos aliases for trigger_exp to use
        xpos = df.x  # noqa (it is used, but in an eval)
        ypos = df.y  # noqa
        df['trigger'] = df.valid & eval(trigger_exp)
        if '.5' in trigger_exp:
            # create columns for "more triggered" conditions if trigger is of form > or < 0.50
            trigger_dir_gt = '>' in trigger_exp
            trigger_plus_vals = [.6, .7, .8, .9] if trigger_dir_gt else [.4, .3, .2, .1]
            for i, newval in enumerate(trigger_plus_vals):
                df['trigger_plus{}'.format(i + 1)] = df.valid & eval(trigger_exp.replace('.5', str(newval)))

        df['frozen'] = df.valid & (df.speed.rolling(window=_freeze_window_size, center=True).max() < _freeze_max_speed)

    def _read_setupfile(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(self.setupfile)
        # parse phases_data
        if 'phases' in self.config and 'phases_data' in self.config['phases']:
            phases_data_str = self.config['phases']['phases_data']
            self.phase_list = eval(phases_data_str)  # uses Phase namedtuple imported from common
        elif 'experiment_args' in self.config:
            # older setup file; look for experiment_args section and build a Phase from that
            onephase = Phase(
                phasenum=1,
                length=int(self.config['experiment_args']['time']),
                dostim=(self.config['at_runtime']['dostim'] == 'True'),
                background=None
            )
            self.phase_list = [onephase]
        else:
            self.phase_list = []  # no clue...

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

    def get_stats_single_table(self, include_phases=False):
        ''' Return a dictionary of key,value pairs with keys as descriptive text. '''
        stats = self.get_stats(include_phases)
        ret = {}
        for dict_name, stats_dict in stats.items():
            entries = {
                "%s - %s" % (key, dict_name) : value
                for key, value in stats_dict.items()
            }
            ret.update(entries)

        return ret

    def get_stats(self, include_phases=False):
        '''
        Return a dictionary of dictionaries, keyed on 'all' and phase names, each containing
        stats for the entire track ('all') or an individual phase.
        '''
        ret = {}
        ret['all'] = self._get_stats_time_range(minutes='all')
        # only include per-phase stats if we have more than one phase
        if include_phases and self.phase_list is not None and len(self.phase_list) > 1:
            start_min = 0
            for phase in self.phase_list:
                phase_stats = self._get_stats_time_range(
                                minutes=(start_min, start_min+phase.length)
                              )
                ret['phase %d' % phase.phasenum] = phase_stats
                start_min += phase.length
        return ret

    def get_exp_stats(self, exp_type):
        if exp_type == 'extinction':
            assert self.phase_list is not None
            return self._get_stats_extinction()
        else:
            return None

    def _get_stats_extinction(self):
        ''' Returns dictionary of statistics for extinction experiments.
            - time until first trigger/incursion
            - time until first 60%, 70%, 80%, 90% reach/incursion
            - since:
                - beginning of phase
                - end of last trigger
        '''
        phase_ends_sec = [60 * t for t in self.phase_starts()[1:]]
        self.df['phase'] = np.searchsorted(phase_ends_sec, self.df.index)

        ret = {}
        for triggercol in 'trigger', 'trigger_plus1', 'trigger_plus2', 'trigger_plus3', 'trigger_plus4':
            ret.update(self._get_stats_extinction_triggercol(triggercol))
        return ret

    def _get_stats_extinction_triggercol(self, triggercol):
        # shorthand
        df = self.df

        ret = {}

        # find first trigger within each phase...
        for phase in self.phase_list:
            phase_ind = (df.phase == phase.phasenum)
            df_phase = df[phase_ind]
            first_trigger_ind = df_phase[triggercol] & (df_phase[triggercol].cumsum() == 1)
            first_trigger_list = df_phase[first_trigger_ind].index.tolist()
            if first_trigger_list:
                # ... from beginning of phase
                first_trigger = first_trigger_list[0]
                first_trigger_delta = first_trigger - 60*self.phase_starts()[phase.phasenum]
                ret['time to first {} from phase start - phase {}'.format(triggercol, phase.phasenum)] = first_trigger_delta
                # ... from end of previous trigger
                if phase.phasenum > 1:
                    # only meaningful for phases after the first
                    prev_phases_ind = (df.phase < phase.phasenum)
                    df_prev_phases = df[prev_phases_ind]
                    # use 'trigger' here, even for calcing time to trigger_plus1, etc.
                    prev_trigger_ind = df_prev_phases.trigger & (df_prev_phases.trigger.cumsum() == df_prev_phases.trigger.cumsum().max())
                    prev_trigger_list = df_prev_phases[prev_trigger_ind].index.tolist()
                    if prev_trigger_list:
                        prev_trigger = prev_trigger_list[0]
                        prev_trigger_delta = first_trigger - prev_trigger
                        ret['time to first {} from previous trigger - phase {}'.format(triggercol, phase.phasenum)] = prev_trigger_delta
        return ret

    def _get_stats_time_range(self, minutes=None):
        ''' Returns dictionary of statistics for the given time range.
            Params:
              minutes:  Tuple of (start_min, end_min) or 'all'.
                        If provided, analysis proceeds from start_min to
                        *beginning* of end_min.
                        If 'all', analysis covers entire dataset.
        '''
        # the dictionary to be returned
        stats = {}

        # shorthand
        df = self.df

        if minutes is not 'all':
            # restrict to rows from the specified time period
            selected = (df.index >= minutes[0]*60) & (df.index < minutes[1]*60)
            df = df[selected]

        total_count = len(df)
        total_time = df.dt.sum()

        stats["#Datapoints"] = total_count
        stats["Total time (sec)"] = total_time

        if total_count == 0:
            # no more stats if no data
            return stats

        # restrict to valid rows for remaining
        df = df[df.valid]

        valid_count = len(df)
        valid_time = df.dt.sum()
        stats["#Valid"] = valid_count
        stats["%Valid datapoints"] = valid_count / total_count
        stats["Valid time (sec)"] = valid_time

        if valid_count == 0:
            # no more stats if no data
            return stats

        trigger_starts, trigger_lens = groups_where(df.trigger)
        trigger_count, trigger_time, _ = self._sum_runs(trigger_starts, trigger_lens, min_runlength=0)

        frozen_starts, frozen_lens = groups_where(df.frozen)
        freeze_count, freeze_time, _ = self._sum_runs(frozen_starts, frozen_lens, min_runlength=_freeze_min_time)

        dist_total = df.dist.sum()
        stats["Total distance traveled (?)"] = dist_total
        # TODO: weight averages by dt of each frame?
        stats["Avg. x coordinate"] = df.x.mean()
        stats["Avg. y coordinate"] = df.y.mean()
        stats["Avg. speed (?/sec)"] = dist_total / valid_time
        stats["Avg. x speed (?/sec)"] = df.dx.abs().sum() / valid_time
        stats["Avg. y speed (?/sec)"] = df.dy.abs().sum() / valid_time
        stats["#Triggers"] = trigger_count
        if trigger_count:
            stats["Total time triggered (sec)"] = trigger_time
            stats["Avg. time per trigger (sec)"] = trigger_time / trigger_count
            stats["Trigger frequency (per min)"] = 60.0*(trigger_count / total_time)
        stats["#Freezes"] = freeze_count
        if freeze_count:
            stats["Total time frozen (sec)"] = freeze_time
            stats["Avg. time per freeze (sec)"] = freeze_time / freeze_count
            stats["Freeze frequency (per min)"] = 60.0*(freeze_count / total_time)

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
