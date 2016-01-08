import argparse
import math
try:
    from ConfigParser import RawConfigParser, MissingSectionHeaderError
except ImportError:
    from configparser import RawConfigParser, MissingSectionHeaderError
import matplotlib.pyplot as plt
from matplotlib import collections, gridspec, lines, patches
import numpy as np

_entry_wait = 2  # min seconds between counted entries to top
_freeze_min_time = 2  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.1  # maximum speed to still consider a "freeze"


# Source: https://gist.github.com/jasonmc/1160951
def _set_foregroundcolor(ax, color):
    '''For the specified axes, sets the color of the frame, major ticks,
    tick labels, axis labels, title and legend
    '''
    for tl in ax.get_xticklines() + ax.get_yticklines():
        tl.set_color(color)
    for spine in ax.spines:
        ax.spines[spine].set_edgecolor(color)
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_color(color)
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_color(color)
    ax.axes.xaxis.label.set_color(color)
    ax.axes.yaxis.label.set_color(color)
    ax.axes.xaxis.get_offset_text().set_color(color)
    ax.axes.yaxis.get_offset_text().set_color(color)
    ax.axes.title.set_color(color)
    lh = ax.get_legend()
    if lh is not None:
        lh.get_title().set_color(color)
        lh.legendPatch.set_edgecolor('none')
        labels = lh.get_texts()
        for lab in labels:
            lab.set_color(color)
    for tl in ax.get_xticklabels():
        tl.set_color(color)
    for tl in ax.get_yticklabels():
        tl.set_color(color)


# Source: https://gist.github.com/jasonmc/1160951
def _set_backgroundcolor(ax, color):
    '''Sets the background color of the current axes (and legend).
    Use 'None' (with quotes) for transparent. To get transparent
    background on saved figures, use:
    pp.savefig("fig1.svg", transparent=True)
    '''
    ax.patch.set_facecolor(color)
    lh = ax.get_legend()
    if lh is not None:
        lh.legendPatch.set_facecolor(color)


class Grapher(object):
    def __init__(self, infile):
        self._trackfile = infile

        time, status, x, y, numpts = np.loadtxt(
            infile,
            delimiter=',',
            unpack=True,
            dtype={'names': ('time','status','x','y','numpts'), 'formats': ('f','S16','f','f','d')},
            converters={2: lambda s: float(s) if s != '.' else -1, 3: lambda s: float(s) if s != '.' else -1}
        )

        # calculate derivatives and other derived values
        #dx = np.gradient(x)
        #dy = np.gradient(y)
        #dt = np.gradient(time)
        dx = np.concatenate( ([0], np.diff(x)) )
        dy = np.concatenate( ([0], np.diff(y)) )
        dt = np.concatenate( ([0], np.diff(time)) )

        if np.min(dt) < 0:
            print("\n[31mWARNING:[m Time travel detected!\n[31mNegative time deltas in following indices:[m "
                  + " ".join(str(x) for x in np.where(dt < 0))
                  + "\n"
                  )

        movement = np.matrix([dx,dy])
        try:
            self._dist = np.linalg.norm(movement, axis=0)
        except TypeError:
            # older version of numpy w/o axis argument
            self._dist = np.array(map(np.linalg.norm, np.transpose(movement)))
        self._speed = np.concatenate( ([0], self._dist[1:] / dt[1:]) )  # ignore invalid 0 entry in dt
        self._theta = np.arctan2(dy, dx)  # reversed params are correct for numpy.arctan2
        #self._dtheta = np.gradient(theta)
        #self._angular_velocity = dtheta / dt

        # produce boolean arrays
        self._valid = (status != 'lost') & (status != 'init') & (np.roll(status, 1) != 'lost') & (np.roll(status, 1) != 'init')  # valid if this index *and* previous are both not 'lost' or 'init'
        self._lost = (status == 'lost') | (status == 'init')
        self._missing = (status == 'missing')
        self._in_top = (y > 0.5)
        self._in_bottom = (y <= 0.5)
        self._in_left25 = (x < 0.25)
        self._in_right25 = (x > 0.75)
        self._frozen = (self._speed < _freeze_max_speed)

        # setup internal data
        self._len = len(time)
        self._time = time
        self._dt = dt
        self._x = x
        self._dx = dx
        self._y = y
        self._dy = dy
        self._numpts = numpts

    def read_setup(self, sections):
        curstats = {}

        setupfile = self._trackfile.split('-track.csv')[0] + '-setup.txt'
        curstats['Setup file'] = setupfile

        parser = RawConfigParser()
        try:
            parser.read(setupfile)
        except MissingSectionHeaderError:
            return curstats

        for section in sections:
            if section not in parser.sections():
                continue

            for key in parser.options(section):
                curstats[section + "__" + key] = parser.get(section, key)

        return curstats

    @property
    def len_minutes(self):
        return int(math.ceil(self._time[-1] / 60.0))

    def get_stats(self, minute=None):
        if minute is not None:
            selected = self._valid & (self._time > minute*60) & (self._time < (minute+1)*60)
        else:
            selected = self._valid

        valid_count = np.sum(selected)

        dist_total = np.sum(self._dist[selected])
        time_total = np.sum(self._dt[selected])

        frozen_starts, frozen_lens = self._groups_where(self._frozen & selected)
        freeze_count, freeze_time, _ = self._sum_runs(frozen_starts, frozen_lens, min_runlength=_freeze_min_time)

        left25_starts, left25_lens = self._groups_where(self._in_left25 & selected)
        left25_count, left25_time, left25_dist = self._sum_runs(left25_starts, left25_lens)

        right25_starts, right25_lens = self._groups_where(self._in_right25 & selected)
        right25_count, right25_time, right25_dist = self._sum_runs(right25_starts, right25_lens)

        top_starts, top_lens = self._groups_where(self._in_top & selected)
        top_count, top_time, top_dist = self._sum_runs(top_starts, top_lens)

        bottom_starts, bottom_lens = self._groups_where(self._in_bottom & selected)
        bottom_count, bottom_time, bottom_dist = self._sum_runs(bottom_starts, bottom_lens)

        # TODO:  cur_turn_time = 0
        # count erratic movements
        # "Erratic movement" = a string of at least _erratic_count 'turns' in less than _erratic_time seconds
        # "Turn" = abs(angular_velocity) > _turn_vel for at least _turn_time seconds
        # TODO

        stats = {}

        if minute is None:
            stats["#Datapoints"] = len(self._valid)
            stats["#Valid"] = valid_count
            stats["%Valid datapoints"] = valid_count / float(len(self._valid))
            stats["Total time (sec)"] = self._time[-1]
            stats["Valid time (sec)"] = time_total

        if selected.any():  # no stats if no data, and avoids "nan" results, as well
            stats["Total distance traveled (?)"] = dist_total
            stats["Avg. x coordinate"] = np.mean(self._x[selected])
            stats["Avg. y coordinate"] = np.mean(self._y[selected])
            stats["Avg. speed (?/sec)"] = dist_total / time_total
            stats["Avg. x speed (?/sec)"] = np.sum(np.abs(self._dx[selected])) / time_total
            stats["Avg. y speed (?/sec)"] = np.sum(np.abs(self._dy[selected])) / time_total
            stats["#Entries to top"] = top_count
            stats["Time in top (sec)"] = top_time
            stats["Time in bottom (sec)"] = bottom_time
            stats["Distance in top (?)"] = top_dist
            stats["Distance in bottom (?)"] = bottom_dist
            if top_count:
                stats["Time of first top entry (sec)"] = self._time[top_starts[0]]
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

        if minute is not None:
            stats = {"Minute %02d - %s" % (minute, key): value for key, value in stats.items()}

        return stats

    @staticmethod
    def _groups_where(vals):
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

    def _sum_runs(self, starts, lens, min_runlength=None, min_wait=None):
        times = self._time[starts+lens] - self._time[starts]
        cumdist = np.cumsum(self._dist)
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

    @staticmethod
    def _speed2color(speed):
        # setup ranges, where 0 maps to first number, 1.0 maps to second
        color_ranges = {
            'r': (0.8, 1.0),
            'g': (0.8, 0.0),
            'b': (0.8, 0.0)
        }

        def scale(inval, color):
            range = color_ranges[color]
            scaled = range[0] + (range[1] - range[0]) * inval
            return min(1, max(0, scaled))  # constrain to 0-1

        r = scale(speed, 'r')
        g = scale(speed, 'g')
        b = scale(speed, 'b')
        return (r,g,b, 0.5)

    def plot(self):
        plt.close('all')

        maxpts = 500
        numplots = 1 + self._len / maxpts

        fig = plt.figure(figsize=(12,2*numplots))
        # make final chart only as wide as needed
        last_width = (self._len % maxpts) / float(maxpts)
        gs = gridspec.GridSpec(
            numplots+1,  # +1 for legend
            2,           # 2 columns for final axis reduced size
            height_ratios=[0.3] + ([1] * numplots),   # 0.2 for 'legend subplot'
            width_ratios=[last_width, 1-last_width],  # all but last will span both columns
        )

        for i in xrange(numplots):
            # all plots but last span both columns,
            # last plot only in the first column, to get the correct width
            if i == numplots - 1:
                ax = plt.subplot(gs[i+1,0])
            else:
                ax = plt.subplot(gs[i+1,:])

            start = i*maxpts
            end = (i+1)*maxpts
            self._subplot(ax, start, end, np.median(self._speed))

        # Draw the legend at the top
        self.draw_legend(plt.subplot(gs[0,:]))

        return fig

    def draw_legend(self, legend_ax):
        # Make a legend with proxy artists
        height_artist = lines.Line2D([],[], color='green')
        numpts_artist = lines.Line2D([],[], color='orange')
        inleft25_artist = patches.Rectangle((0,0), 1, 1, fc='purple', ec='None')
        inright25_artist = patches.Rectangle((0,0), 1, 1, fc='pink', ec='None')
        intop_artist = patches.Rectangle((0,0), 1, 1, fc='blue', ec='None')
        frozen_artist = patches.Rectangle((0,0), 1, 1, fc='lightblue', ec='None')
        missing_artist = patches.Rectangle((0,0), 1, 1, fc='yellow', ec='None')
        lost_artist = patches.Rectangle((0,0), 1, 1, fc='red', ec='None')
        # Place it in center of top "subplot" area
        legend_ax.legend(
            [height_artist, numpts_artist, inleft25_artist, inright25_artist, intop_artist, frozen_artist, missing_artist, lost_artist],
            ['Height of fish', '# Detection pts', 'In left 25%', 'In right 25%', 'In top 50%', 'Frozen', 'Missing', 'Lost'],
            loc='center',
            ncol=4,
        )
        legend_ax.axis('off')
        self._format_axis(legend_ax)

    def plot_leftright(self, addplot=False):
        if not addplot:
            plt.close('all')
            plt.figure(figsize=(6, 4))

        left25_starts, left25_lens = self._groups_where(self._in_left25)

        color = 'blue' if addplot else 'purple'
        plt.step(self._time[left25_starts], range(1, len(left25_starts)+1), where='post', color=color)

        right25_starts, right25_lens = self._groups_where(self._in_right25)

        color = 'cyan' if addplot else 'pink'
        plt.step(self._time[right25_starts], range(1, len(right25_starts)+1), where='post', color=color)

        if not addplot:
            self._format_axis(plt.gca())
            plt.title("Cumulative Entries to Left/Right 25%")
            plt.xlabel("Time (seconds)")
            plt.ylabel("Cumulative entries")
            plt.xlim(0, self._time[-1])
            plt.legend(["Left", "Right"], fontsize=8, loc=2)

    def plot_heatmap(self, numplots=1):
        plt.close('all')
        plt.figure(figsize=(4*numplots, 4))
        for i in range(numplots):
            start = i * len(self._x) / numplots
            end = (i+1) * len(self._x) / numplots
            ax = plt.subplot(1, numplots, i+1)
            if numplots > 1:
                ax.axes.get_xaxis().set_visible(False)
                ax.axes.get_yaxis().set_visible(False)
            else:
                self._format_axis(ax)
            # imshow expects y,x for the image, but x,y for the extents,
            # so we have to manage that here...
            nbins = 50
            #heatmap, yedges, xedges = np.histogram2d(self._y[start:end], self._x[start:end], bins=nbins)
            bins = np.concatenate( (np.arange(0,1.0,1.0/nbins), [1.0]) )
            heatmap, yedges, xedges = np.histogram2d(self._y[start:end], self._x[start:end], bins=bins)
            extent = [xedges[0],xedges[-1], yedges[0], yedges[-1]]
            # make sure we always show the full extent of the tank and the full extent of the data,
            # whichever is wider.
            ax.set_xlim(min(0, xedges[0]), max(1, xedges[-1]))
            ax.set_ylim(min(0, yedges[0]), max(1, yedges[-1]))
            ax.imshow(heatmap, extent=extent, cmap=plt.get_cmap('afmhot'), origin='lower', interpolation='nearest')

    def _subplot(self, ax, start, end, median_speed):
        time = self._time[start:end]
        theta = self._theta[start:end]
        speed = self._speed[start:end]
        #valid = self._valid[start:end]
        lost = self._lost[start:end]
        missing = self._missing[start:end]
        frozen = self._frozen[start:end]
        in_left25 = self._in_left25[start:end]
        in_right25 = self._in_right25[start:end]
        in_top = self._in_top[start:end]
        #x = self._x[start:end]
        y = self._y[start:end]
        numpts = self._numpts[start:end]

        # Format nicely
        self._format_axis(ax)
        ax.axes.get_yaxis().set_visible(False)

        # Get set axes (specifically, we don't want the y-axis to be autoscaled for us)
        ax.axis([time[0], time[-1], -1, 1])

        # Mark lost/missing sections
        lost_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.9, -1.0,
            lost,
            edgecolors='none',
            facecolors='red',
        )
        ax.add_collection(lost_collection)
        missing_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.9, -1.0,
            missing,
            edgecolors='none',
            facecolors='yellow',
        )
        ax.add_collection(missing_collection)

        # Mark frozen sections
        frozen_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.8, -0.85,
            frozen,
            edgecolors='none',
            facecolors='lightblue',
        )
        ax.add_collection(frozen_collection)

        # Mark in-top sections
        intop_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.7, -0.75,
            in_top,
            edgecolors='none',
            facecolors='blue',
        )
        ax.add_collection(intop_collection)

        # Mark in-left25 sections
        inleft25_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.6, -0.65,
            in_left25,
            edgecolors='none',
            facecolors='purple',
        )
        ax.add_collection(inleft25_collection)

        # Mark in-right25 sections
        inright25_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.6, -0.65,
            in_right25,
            edgecolors='none',
            facecolors='pink',
        )
        ax.add_collection(inright25_collection)

        # Plot height
        ax.plot(time, y*2-1, color='green', label='Height of fish')

        # Plot numpts (scaled so 0 = bottom, 20 = top of subplot)
        ax.plot(time, -1+(numpts/10.0), color='orange', label='# detected points')

        # Add stick plot of movement (where valid)
        ax.quiver(
            time, [0] * len(time),
            speed*np.cos(theta), speed*np.sin(theta),
            color=[self._speed2color(s) for s in speed],
            scale=1,  # scale all to a speed of 1, which should be close to max (tank is 1.0x1.0)
            scale_units='y',
            width=0.01,
            units='inches',
            headlength=0, headwidth=0, headaxislength=0     # no arrowheads
        )

    @staticmethod
    def _format_axis(ax):
        _set_foregroundcolor(ax, '0.5')
        _set_backgroundcolor(ax, '0.08')
        for spine in ax.spines:
            ax.spines[spine].set_visible(False)

    @staticmethod
    def _format_figure():
        plt.gcf().patch.set_facecolor('0.12')
        plt.tight_layout()

    def show(self):
        self._format_figure()
        plt.show()

    def savefig(self, outfile):
        self._format_figure()
        plt.savefig(outfile, facecolor=plt.gcf().get_facecolor(), edgecolor='none')


def main():
    parser = argparse.ArgumentParser(description='Analyze zebrafish Skinner box experiment tracks.')
    parser.add_argument('infile', type=str)
    parser.add_argument('outfile', type=str, nargs='?')
    parser.add_argument('-H', '--heat', action='store_true')
    parser.add_argument('--heat-num', type=int, default=1)
    parser.add_argument('-L', '--leftright', action='store_true')
    args = parser.parse_args()

    g = Grapher(args.infile)

    stats = g.get_stats()
    maxlen = max(len(key) for key in stats.keys())
    for key, val in stats.items():
        if type(val) is np.float32 or type(val) is np.float64:
            val = "%0.3f" % val
        print ("%*s: %s") % (maxlen, key, str(val))

    if args.heat:
        g.plot_heatmap(args.heat_num)
    elif args.leftright:
        g.plot_leftright()
    else:
        g.plot()

    if args.outfile is None:
        g.show()
    else:
        g.savefig(args.outfile)

if __name__ == '__main__':
    main()
