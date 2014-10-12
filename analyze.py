import matplotlib.pyplot as plt
from matplotlib import collections, gridspec, lines, patches
import numpy as np
import sys

_entry_wait = 1  # min seconds between counted entries to top
_freeze_min_time = 0.1  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.01  # maximum speed to still consider a "freeze"


# Source: https://gist.github.com/jasonmc/1160951
def set_foregroundcolor(ax, color):
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
def set_backgroundcolor(ax, color):
    '''Sets the background color of the current axes (and legend).
    Use 'None' (with quotes) for transparent. To get transparent
    background on saved figures, use:
    pp.savefig("fig1.svg", transparent=True)
    '''
    ax.patch.set_facecolor(color)
    lh = ax.get_legend()
    if lh is not None:
        lh.legendPatch.set_facecolor(color)


def plot(time, theta, speed, valid, lost, missing, frozen, in_top, x, y, numpts):
    maxpts = 500
    numplots = 1 + len(time) / maxpts

    fig = plt.figure(figsize=(12,2*numplots))
    # make final chart only as wide as needed
    last_width = (len(time) % maxpts) / float(maxpts)
    gs = gridspec.GridSpec(
        numplots+1, 2,
        height_ratios=[0.2] + ([1] * numplots),   # 0.2 for 'legend subplot'
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
        subplot(ax, time[start:end], theta[start:end], np.median(speed), speed[start:end], valid[start:end], lost[start:end], missing[start:end], frozen[start:end], in_top[start:end], x[start:end], y[start:end], numpts[start:end])

    # Make a legend with proxy artists
    height_artist = lines.Line2D([],[], color='green')
    intop_artist = patches.Rectangle((0,0), 1, 1, fc='blue', ec='None')
    frozen_artist = patches.Rectangle((0,0), 1, 1, fc='lightblue', ec='None')
    missing_artist = patches.Rectangle((0,0), 1, 1, fc='yellow', ec='None')
    lost_artist = patches.Rectangle((0,0), 1, 1, fc='red', ec='None')
    # Place it in center of top "subplot" area
    legend_ax = plt.subplot(gs[0,:])
    legend_ax.legend(
        [height_artist, intop_artist, frozen_artist, missing_artist, lost_artist],
        ['Height of fish', 'In top 50%', 'Frozen', 'Missing', 'Lost'],
        loc='center',
        ncol=5,
    )
    legend_ax.axis('off')
    set_backgroundcolor(legend_ax, 'None')
    set_foregroundcolor(legend_ax, '0.6')

    # Format nicely
    fig.patch.set_facecolor('black')
    plt.tight_layout()

    plt.show()
    fig.savefig('plot.svg', facecolor=fig.get_facecolor(), edgecolor='none')


def speed2color(speed, median_speed):
    cutoff = median_speed*5
    r = min(1, 0.8+speed/cutoff)
    g = max(0, 0.8-speed/cutoff)
    b = g
    return (r,g,b, 0.5)


def subplot(ax, time, theta, median_speed, speed, valid, lost, missing, frozen, in_top, x, y, numpts):
    # Format nicely
    set_foregroundcolor(ax, '0.6')
    set_backgroundcolor(ax, '0.08')
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

    # Plot numpts (scaled so 0 = bottom, 10 = top of subplot)
    ax.plot(time, -1+(numpts/5.0), color='orange', label='# detected points')

    # Add stick plot of movement (where valid)
    ax.quiver(
        time, [0] * len(time),
        speed*np.cos(theta), speed*np.sin(theta),
        color=[speed2color(s, median_speed) for s in speed],
        scale=median_speed*4,
        scale_units='y',
        width=0.01,
        units='inches',
        headlength=0, headwidth=0, headaxislength=0     # no arrowheads
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: %s track.csv" % sys.argv[0])
        sys.exit(1)

    fname = sys.argv[1]

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
    in_top = y > 0.5
    frozen = speed < _freeze_max_speed

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

    cur_turn_time = 0

    distance_total = 0
    time_total_valid = 0

    for i in xrange(1, len(time)):
        if not valid[i]:
            # cancel any ongoing 'events'
            if cur_freeze_time:
                freeze_count -= 1
                total_freeze_time -= cur_freeze_time
                cur_freeze_time = 0
            if cur_turn_time:
                # TODO
                pass
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

    plot(time, theta, np.where(valid, speed, 0), valid, lost, missing, frozen, in_top, x, y, numpts)

if __name__ == '__main__':
    main()
