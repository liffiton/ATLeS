import argparse
import matplotlib.pyplot as plt
from matplotlib import collections, gridspec, lines, patches
import numpy as np

_entry_wait = 1  # min seconds between counted entries to top
_freeze_min_time = 1  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.1  # maximum speed to still consider a "freeze"


class Grapher(object):
    def load(self, infile):
        time, status, x, y, numpts = np.loadtxt(
            infile,
            delimiter=',',
            unpack=True,
            dtype={'names': ('time','status','x','y','numpts'), 'formats': ('f','S16','f','f','d')}
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
            dist = np.linalg.norm(movement, axis=0)
        except TypeError:
            # older version of numpy w/o axis argument
            dist = map(np.linalg.norm, np.transpose(movement))
        speed = np.concatenate( ([0], dist[1:] / dt[1:]) )  # ignore invalid 0 entry in dt
        theta = np.arctan2(dy, dx)  # reversed params are correct for numpy.arctan2
        #dtheta = np.gradient(theta)
        #angular_velocity = dtheta / dt

        # produce boolean arrays
        valid = (status != 'lost') & (np.roll(status, 1) != 'lost')  # valid if this index *and* previous are both not 'lost'
        valid_count = np.sum(valid)
        lost = status == 'lost'
        missing = status == 'missing'
        in_top = valid & (y > 0.5)
        in_left25 = valid & (x < 0.25)
        frozen = valid & (speed < _freeze_max_speed)

        # setup internal data
        self._len = len(time)
        self._time = time
        self._theta = theta
        self._dist = dist
        self._speed = speed
        self._valid = valid
        self._lost = lost
        self._missing = missing
        self._frozen = frozen
        self._in_top = in_top
        self._in_left25 = in_left25
        self._x = x
        self._y = y
        self._numpts = numpts

        dist_total = np.sum(dist[valid])
        time_total = np.sum(dt[valid])

        frozen_starts, frozen_lens = self._groups_where(frozen)
        freeze_count, freeze_time, _ = self._sum_runs(frozen_starts, frozen_lens, min_runlength=_freeze_min_time)

        left25_starts, left25_lens = self._groups_where(in_left25)
        left25_count, left25_time, left25_dist = self._sum_runs(left25_starts, left25_lens)

        top_starts, top_lens = self._groups_where(in_top)
        top_count, top_time, top_dist = self._sum_runs(top_starts, top_lens)

        #bottom_starts, bottom_lens = self._groups_where(y < 0.5)
        #bottom_count, bottom_time, bottom_dist = self._sum_runs(bottom_starts, bottom_lens)
        bottom_time = time_total - top_time
        bottom_dist = dist_total - top_dist

        # TODO:  cur_turn_time = 0
        # count erratic movements
        # "Erratic movement" = a string of at least _erratic_count 'turns' in less than _erratic_time seconds
        # "Turn" = abs(angular_velocity) > _turn_vel for at least _turn_time seconds
        # TODO

        print "#Datapoints: %d" % len(valid)
        print "#Valid: %d" % valid_count
        print "%%Valid datapoints: %0.3f" % (valid_count / float(len(valid)))
        print "Total time: %0.2f seconds" % time[-1]
        print "Valid time: %0.2f seconds" % time_total
        print
        print "Total distance traveled: %0.2f [units]" % (dist_total)
        print "Average velocity: %0.3f [units]/second" % (dist_total / time_total)
        print
        print "#Entries to top: %d" % top_count
        if top_count:
            print "Time of first entry: %0.2f seconds" % (time[top_starts[0]])
        print
        print "Time in top:    %0.2f seconds" % top_time
        print "Time in bottom: %0.2f seconds" % bottom_time
        if bottom_time:
            print "Top/bottom time ratio: %0.3f" % (top_time/bottom_time)
        if top_count:
            print "Avg. time per entry: %0.2f seconds" % (top_time / top_count)
        print
        print "Distance in top:    %0.3f [units]" % top_dist
        print "Distance in bottom: %0.3f [units]" % bottom_dist
        if bottom_dist:
            print "Top/bottom distance ratio: %0.3f" % (top_dist/bottom_dist)
        if top_count:
            print "Avg. distance per entry: %0.3f [units]" % (top_dist / top_count)
        print
        print "#Freezes: %d" % freeze_count
        if freeze_count:
            print "Total time frozen: %0.3f seconds" % freeze_time
            print "Avg. time per freeze: %0.3f seconds" % (freeze_time / freeze_count)
            print "Freeze frequency: %0.2f per minute" % (60.0*(freeze_count / time_total))

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

    # Source: https://gist.github.com/jasonmc/1160951
    @staticmethod
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
    @staticmethod
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

    @staticmethod
    def _speed2color(speed, median_speed):
        cutoff = median_speed*5
        r = max(0,min(1, 0.8+speed/cutoff))
        g = min(1,max(0, 0.8-speed/cutoff))
        b = g
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
        intop_artist = patches.Rectangle((0,0), 1, 1, fc='blue', ec='None')
        frozen_artist = patches.Rectangle((0,0), 1, 1, fc='lightblue', ec='None')
        missing_artist = patches.Rectangle((0,0), 1, 1, fc='yellow', ec='None')
        lost_artist = patches.Rectangle((0,0), 1, 1, fc='red', ec='None')
        # Place it in center of top "subplot" area
        legend_ax.legend(
            [height_artist, numpts_artist, inleft25_artist, intop_artist, frozen_artist, missing_artist, lost_artist],
            ['Height of fish', '# Detection pts', 'In left 25%', 'In top 50%', 'Frozen', 'Missing', 'Lost'],
            loc='center',
            ncol=4,
        )
        legend_ax.axis('off')
        self._set_backgroundcolor(legend_ax, 'None')
        self._set_foregroundcolor(legend_ax, '0.6')

    def plot_heatmap(self, numplots=1):
        plt.close('all')
        plt.figure(figsize=(4, 4*numplots))
        for i in range(numplots):
            start = i * len(self._x) / numplots
            end = (i+1) * len(self._x) / numplots
            ax = plt.subplot(numplots, 1, i+1)
            ax.axes.get_xaxis().set_visible(False)
            ax.axes.get_yaxis().set_visible(False)
            # imshow expects y,x for the image, but x,y for the extents,
            # so we have to manage that here...
            nbins = 50
            #heatmap, yedges, xedges = np.histogram2d(self._y[start:end], self._x[start:end], bins=nbins)
            bins = np.concatenate( (np.arange(0,1.0,1.0/nbins), [1.0]) )
            heatmap, yedges, xedges = np.histogram2d(self._y[start:end], self._x[start:end], bins=bins)
            extent = [xedges[0],xedges[-1], yedges[0], yedges[-1]]
            # make sure we always show the full extent of the tank, regardless of where the data lies in it
            ax.set_xlim(0,1)
            ax.set_ylim(0,1)
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
        in_top = self._in_top[start:end]
        #x = self._x[start:end]
        y = self._y[start:end]
        numpts = self._numpts[start:end]

        # Format nicely
        self._set_foregroundcolor(ax, '0.6')
        self._set_backgroundcolor(ax, '0.08')
        for spine in ax.spines:
            ax.spines[spine].set_visible(False)
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

        # Plot height
        ax.plot(time, y, color='green', label='Height of fish')

        # Plot numpts (scaled so 0 = bottom, 20 = top of subplot)
        ax.plot(time, -1+(numpts/10.0), color='orange', label='# detected points')

        # Add stick plot of movement (where valid)
        ax.quiver(
            time, [0] * len(time),
            speed*np.cos(theta), speed*np.sin(theta),
            color=[self._speed2color(s, median_speed) for s in speed],
            scale=median_speed*4,
            scale_units='y',
            width=0.01,
            units='inches',
            headlength=0, headwidth=0, headaxislength=0     # no arrowheads
        )

    def format(self):
        # Format nicely
        plt.gcf().patch.set_facecolor('0.1')
        plt.tight_layout()

    def show(self):
        self.format()
        plt.show()

    def savefig(self, outfile):
        self.format()
        plt.savefig(outfile, facecolor=plt.gcf().get_facecolor(), edgecolor='none')


def main():
    parser = argparse.ArgumentParser(description='Analyze zebrafish Skinner box experiment logs.')
    parser.add_argument('infile', type=str)
    parser.add_argument('outfile', type=str, nargs='?')
    parser.add_argument('-H', '--heat-only', action='store_true')
    parser.add_argument('--heat-num', type=int, default=1)
    args = parser.parse_args()

    g = Grapher()
    g.load(args.infile)

    if args.heat_only:
        g.plot_heatmap(args.heat_num)
    else:
        g.plot()

    if args.outfile is None:
        g.show()
    else:
        g.savefig(args.outfile)

if __name__ == '__main__':
    main()
