import matplotlib.pyplot as plt
from matplotlib import collections, gridspec, lines, patches
import numpy as np
import sys

_entry_wait = 1  # min seconds between counted entries to top
_freeze_min_time = 1  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.3  # maximum speed to still consider a "freeze"


class Grapher(object):
    def __init__(self, time, theta, speed, valid, lost, missing, frozen, in_top, x, y, numpts):
        self._len = len(time)
        self._time = time
        self._theta = theta
        self._speed = speed
        self._valid = valid
        self._lost = lost
        self._missing = missing
        self._frozen = frozen
        self._in_top = in_top
        self._x = x
        self._y = y
        self._numpts = numpts

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
        maxpts = 500
        numplots = 1 + self._len / maxpts

        fig = plt.figure(figsize=(12,2*numplots))
        # make final chart only as wide as needed
        last_width = (self._len % maxpts) / float(maxpts)
        gs = gridspec.GridSpec(
            numplots+2,  # +1 for legend, +1 for heatmap
            2,           # 2 columns for final axis reduced size
            height_ratios=[0.2] + ([1] * numplots) + [5],   # 0.2 for 'legend subplot', 5 for heatmap
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

        # Draw the heatmap at the bottom
        self.plot_heatmap(plt.subplot(gs[-1,:]))

        # Format nicely
        fig.patch.set_facecolor('black')
        plt.tight_layout()

        return fig

    def draw_legend(self, legend_ax):
        # Make a legend with proxy artists
        height_artist = lines.Line2D([],[], color='green')
        numpts_artist = lines.Line2D([],[], color='orange')
        intop_artist = patches.Rectangle((0,0), 1, 1, fc='blue', ec='None')
        frozen_artist = patches.Rectangle((0,0), 1, 1, fc='lightblue', ec='None')
        missing_artist = patches.Rectangle((0,0), 1, 1, fc='yellow', ec='None')
        lost_artist = patches.Rectangle((0,0), 1, 1, fc='red', ec='None')
        # Place it in center of top "subplot" area
        legend_ax.legend(
            [height_artist, numpts_artist, intop_artist, frozen_artist, missing_artist, lost_artist],
            ['Height of fish', '# Detection pts', 'In top 50%', 'Frozen', 'Missing', 'Lost'],
            loc='center',
            ncol=6,
        )
        legend_ax.axis('off')
        self._set_backgroundcolor(legend_ax, 'None')
        self._set_foregroundcolor(legend_ax, '0.6')

    def plot_heatmap(self, heatmap_ax):
        # imshow expects y,x for the image, but x,y for the extents,
        # so we have to manage that here...
        heatmap, yedges, xedges = np.histogram2d(self._y, self._x, bins=100)
        #extent = [0,1,0,1]
        extent = [min(0,xedges[0]), max(1,xedges[-1]), min(0,yedges[0]), max(1,yedges[-1])]
        heatmap_ax.imshow(heatmap, extent=extent, cmap=plt.get_cmap('afmhot'), origin='lower', interpolation='nearest')

    def _subplot(self, ax, start, end, median_speed):
        time = self._time[start:end]
        theta = self._theta[start:end]
        speed = self._speed[start:end]
        #valid = self._valid[start:end]
        lost = self._lost[start:end]
        missing = self._missing[start:end]
        frozen = self._frozen[start:end]
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
            -0.8, -0.85,
            lost,
            edgecolors='none',
            facecolors='red',
        )
        ax.add_collection(lost_collection)
        missing_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.8, -0.85,
            missing,
            edgecolors='none',
            facecolors='yellow',
        )
        ax.add_collection(missing_collection)

        # Mark frozen sections
        frozen_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.75, -0.8,
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


def main():
    if len(sys.argv) < 2:
        print("Usage: %s track.csv [outfile] [heat]" % sys.argv[0])
        sys.exit(1)

    fname = sys.argv[1]

    # hack for now
    if len(sys.argv) > 2:
        outname = sys.argv[2]
    else:
        outname = 'plot.svg'
    heat_only = len(sys.argv) > 3

    time, status, x, y, numpts = np.loadtxt(
        fname,
        delimiter=',',
        unpack=True,
        dtype={'names': ('time','status','x','y','numpts'), 'formats': ('f','S16','f','f','d')}
    )

    # calculate derivatives and other derived values
    dx = np.gradient(x)
    dy = np.gradient(y)
    dt = np.gradient(time)

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
    speed = dist / dt
    theta = np.arctan2(dy, dx)  # reversed params are correct for numpy.arctan2
    #dtheta = np.gradient(theta)
    #angular_velocity = dtheta / dt

    # produce boolean arrays
    valid = (status != 'lost') & (np.roll(status, 1) != 'lost')  # valid if this index *and* previous are both not 'lost'
    valid_count = np.sum(valid)
    lost = status == 'lost'
    missing = status == 'missing'
    in_top = valid & (y > 0.5)
    frozen = valid & (speed < _freeze_max_speed)

    # initialize counters, etc.
    last_entry = None
    first_entry = None
    entry_count = 0

    time_in_top = 0
    time_in_bottom = 0

    distance_in_top = 0
    distance_in_bottom = 0

    cur_freeze_time = 0
    total_freeze_time = 0
    freeze_count = 0

    # TODO:  cur_turn_time = 0

    distance_total = 0
    time_total_valid = 0

    for i in xrange(1, len(time)):
        if not valid[i]:
            continue

        distance_total += dist[i]
        time_total_valid += dt[i]

        # count entries to top
        if in_top[i] and not in_top[i-1] and (last_entry is None or time[i] - last_entry > _entry_wait):
            if first_entry is None:
                first_entry = time[i]
            last_entry = time[i]
            entry_count += 1

        # sum time and distance in top/bottom
        if in_top[i]:
            time_in_top += dt[i]
            distance_in_top += dist[i]
        else:
            time_in_bottom += dt[i]
            distance_in_bottom += dist[i]

        # count freezes
        # "Freeze" = speed < _freeze_max_speed for at least _freeze_min_time seconds
        if frozen[i]:
            if not frozen[i-1]:
                # start of a freeze
                cur_freeze_time = 0
                freeze_count += 1
            total_freeze_time += dt[i]
            cur_freeze_time += dt[i]
        elif frozen[i-1]:
            # end of a freeze
            if cur_freeze_time < _freeze_min_time:
                # don't count this one
                freeze_count -= 1
                total_freeze_time -= cur_freeze_time

        # count erratic movements
        # "Erratic movement" = a string of at least _erratic_count 'turns' in less than _erratic_time seconds
        # "Turn" = abs(angular_velocity) > _turn_vel for at least _turn_time seconds
        # TODO

    print "#Datapoints: %d" % len(valid)
    print "#Valid: %d" % valid_count
    print "%%Valid datapoints: %0.3f" % (valid_count / float(len(valid)))
    print "Total time: %0.2f seconds" % time[-1]
    print "Valid time: %0.2f seconds" % time_total_valid
    print
    print "Total distance traveled: %0.2f [units]" % (distance_total)
    print "Average velocity: %0.3f [units]/second" % (distance_total / time_total_valid)
    print
    print "#Entries to top: %d" % entry_count
    if entry_count:
        print "Time of first entry: %0.2f seconds" % (first_entry)
    print
    print "Time in top:    %0.2f seconds" % time_in_top
    print "Time in bottom: %0.2f seconds" % time_in_bottom
    if time_in_bottom:
        print "Top/bottom time ratio: %0.3f" % (time_in_top/time_in_bottom)
    if entry_count:
        print "Avg. time per entry: %0.2f seconds" % (time_in_top / entry_count)
    print
    print "Distance in top:    %0.3f [units]" % distance_in_top
    print "Distance in bottom: %0.3f [units]" % distance_in_bottom
    if distance_in_bottom:
        print "Top/bottom distance ratio: %0.3f" % (distance_in_top/distance_in_bottom)
    if entry_count:
        print "Avg. distance per entry: %0.3f [units]" % (distance_in_top / entry_count)
    print
    print "#Freezes: %d" % freeze_count
    if freeze_count:
        print "Total time frozen: %0.3f seconds" % total_freeze_time
        print "Avg. time per freeze: %0.3f seconds" % (total_freeze_time / freeze_count)
        print "Freeze frequency: %0.2f per minute" % (60.0*(freeze_count / time_total_valid))

    g = Grapher(time, theta, np.where(valid, speed, 0), valid, lost, missing, frozen, in_top, x, y, numpts)

    if heat_only:
        fig = plt.figure(figsize=(6,6))
        g.plot_heatmap(plt.subplot())
    else:
        fig = g.plot()

    plt.show()
    fig.savefig(outname, facecolor=fig.get_facecolor(), edgecolor='none')

if __name__ == '__main__':
    main()
