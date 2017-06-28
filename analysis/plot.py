import math
import os
import re

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import collections, gridspec, lines, patches
import numpy as np

from analysis import heatmaps, process


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


def _format_axis(ax):
    _set_foregroundcolor(ax, '0.5')
    _set_backgroundcolor(ax, '0.08')
    # drop plot borders
    for spine in ax.spines:
        ax.spines[spine].set_visible(False)


def _format_figure(fig):
    fig.patch.set_facecolor('0.12')
    plt.tight_layout()


def show():
    ''' Shows the current figure (on screen, if using a GUI backend).
        Create a plot first using a TrackPlotter object. '''
    fig = plt.gcf()
    _format_figure(fig)
    plt.show()
    plt.close('all')


def savefig(outfile):
    ''' Saves the current figure to the given filename.
        Format is inferred from the file extension.
        Large (tall) figures are broken into multiple images (vertical tiles).
        Create a plot first using a TrackPlotter object. '''
    fig = plt.gcf()
    _format_figure(fig)
    # A bit of an ugly hack to split giant images into multiple parts
    max_height = 100
    # plot height in inches
    height = fig.get_window_extent().transformed(fig.dpi_scale_trans.inverted()).height
    if height > max_height:
        numparts = int(height / max_height) + 1
        for i in range(numparts):
            filename = re.sub(r"(\.[^\.]+)$", r"%02d\1" % (numparts-i), outfile)
            bbox = matplotlib.transforms.Bbox.from_extents([0,i*max_height,12,min(height,(i+1)*max_height)])
            plt.savefig(filename, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches=bbox)
    else:
        plt.savefig(outfile, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close('all')


class TrackPlotter(object):
    def __init__(self, track_processor, dbgframes=None):
        self._track = track_processor
        self._dbgframes = dbgframes

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

    def plot_trace(self):
        maxpts = 500
        numplots = int(math.ceil(float(self._track.len) / maxpts))

        fig = plt.figure(figsize=(12,1+2*numplots))
        # make final chart only as wide as needed
        last_width = (self._track.len % maxpts) / float(maxpts)
        if last_width == 0.0:
            # Final chart may be full-width
            last_width = 1.0
        gs = gridspec.GridSpec(
            numplots+1,  # +1 for legend
            2,           # 2 columns for final axis reduced size
            height_ratios=[0.5] + ([1] * numplots),   # 0.5 for 'legend subplot'
            width_ratios=[last_width, 1-last_width],  # all but last will span both columns
        )

        for i in range(numplots):
            # all plots but last span both columns,
            # last plot only in the first column, to get the correct width
            if i == numplots - 1:
                ax = plt.subplot(gs[i+1,0])
            else:
                ax = plt.subplot(gs[i+1,:])

            start = i*maxpts
            end = (i+1)*maxpts
            self._plot_trace_portion(ax, start, end, np.median(self._track.speed))

        # Draw the legend at the top
        self.draw_legend(plt.subplot(gs[0,:]))

        return fig

    def draw_legend(self, legend_ax):
        # Make a legend with proxy artists
        xpos_artist = lines.Line2D([],[], color='orange')
        ypos_artist = lines.Line2D([],[], color='limegreen')
        numpts_artist = lines.Line2D([],[], color='purple', linewidth=1)
        #inleft25_artist = patches.Rectangle((0,0), 1, 1, fc='purple', ec='None')
        #inright25_artist = patches.Rectangle((0,0), 1, 1, fc='pink', ec='None')
        intop_artist = patches.Rectangle((0,0), 1, 1, fc='blue', ec='None')
        frozen_artist = patches.Rectangle((0,0), 1, 1, fc='lightblue', ec='None')
        missing_artist = patches.Rectangle((0,0), 1, 1, fc='yellow', ec='None')
        lost_artist = patches.Rectangle((0,0), 1, 1, fc='red', ec='None')
        # Place it in center of top "subplot" area
        legend_ax.legend(
            [xpos_artist, ypos_artist, numpts_artist,
                #inleft25_artist, inright25_artist,
                intop_artist, frozen_artist, missing_artist, lost_artist],
            ['x-pos', 'y-pos', '# Detection pts',
                #'In left 25%', 'In right 25%',
                'In top 50%', 'Frozen', 'Missing', 'Lost'],
            loc='center',
            fontsize=12,
            ncol=4,
        )
        legend_ax.axis('off')
        _format_axis(legend_ax)

    def plot_leftright(self, addplot=False):
        if not addplot:
            plt.figure(figsize=(6, 4))

        ax = plt.gca()

        left25_starts, left25_lens = process.groups_where(self._track.in_left25)

        color = 'blue' if addplot else 'purple'
        ax.step(self._track.time[left25_starts], range(1, len(left25_starts)+1), where='post', color=color)

        right25_starts, right25_lens = process.groups_where(self._track.in_right25)

        color = 'cyan' if addplot else 'pink'
        ax.step(self._track.time[right25_starts], range(1, len(right25_starts)+1), where='post', color=color)

        if not addplot:
            _format_axis(ax)
            ax.set_title("Cumulative Entries to Left/Right 25%")
            ax.set_xlabel("Time (seconds)")
            ax.set_ylabel("Cumulative entries")
            ax.set_xlim(0, self._track.time[-1])
            ax.legend(["Left", "Right"], fontsize=8, loc=2)

    def plot_x_fft(self, numplots=1):
        fig, axes = plt.subplots(1, numplots, squeeze=False, figsize=(4*numplots, 4))
        for i, ax in enumerate(axes[0]):
            start = i * len(self._track.x) // numplots
            end = (i+1) * len(self._track.x) // numplots
            ax.set_yscale('log')
            ax.set_ylim([0.1,1000])
            _format_axis(ax)
            #ax.axes.get_xaxis().set_visible(False)
            #ax.axes.get_yaxis().set_visible(False)

            # compute fft
            window = np.blackman(end-start)
            fft = np.fft.rfft(self._track.x[start:end] * window)
            freq = np.fft.rfftfreq(n=end-start, d=1.0/10)

            ax.plot(freq[:len(freq)//2], abs(fft[:len(fft)//2]))

    def plot_invalidheatmap(self):
        title = "Map of shame (loc of invalid data)"

        plt.figure(figsize=(4, 4))
        ax = plt.gca()

        ax.set_title(title)
        _format_axis(ax)

        nbins = 50

        badpoints = (self._track.valid != True)  # noqa: E712
        heatmaps.plot_heatmap(ax, self._track.x[badpoints], self._track.y[badpoints], nbins=nbins)

    def plot_heatmap(self, plot_type='overall'):
        assert plot_type in ('per-minute', 'per-phase', 'overall')
        if plot_type == 'per-minute':
            numplots = int(math.ceil(self._track.time[-1] / 60.0))
        elif plot_type == 'per-phase':
            numplots = self._track.num_phases()
            phase_starts = self._track.phase_starts()
            phase_ends = phase_starts[1:] + [2**30]
        elif plot_type == 'overall':
            numplots = 1

        numrows = int(math.ceil(numplots / 10.0))
        if plot_type == 'overall':
            plt.figure(figsize=(4, 4))
        else:
            plt.figure(figsize=(2*min(numplots, 10), 2*numrows))

        for i in range(numplots):
            if plot_type == 'per-minute':
                start_min = i
                end_min = i+1
                title = "{}:00-{}:00".format(start_min, end_min)
            elif plot_type == 'per-phase':
                start_min = phase_starts[i]
                end_min = phase_ends[i]
                title = "Phase {} ({}:00-{}:00)".format(i, start_min, end_min)
            elif plot_type == 'overall':
                start_min = 0
                end_min = 2**30
                title = "Overall heatmap"
            selected = (self._track.time >= start_min*60) & (self._track.time < end_min*60)

            ax = plt.subplot(numrows, min(numplots, 10), i+1)

            if numplots > 1:
                ax.axes.get_xaxis().set_visible(False)
                ax.axes.get_yaxis().set_visible(False)

            _format_axis(ax)

            ax.set_title(title)

            nbins = 50
            heatmaps.plot_heatmap(ax, self._track.x[selected], self._track.y[selected], nbins=nbins)

    def _plot_trace_portion(self, ax, start, end, median_speed):
        time = self._track.time[start:end]
        #theta = self._track.theta[start:end]
        #speed = self._track.speed[start:end]
        #valid = self._track.valid[start:end]
        lost = self._track.lost[start:end]
        missing = self._track.missing[start:end]
        frozen = self._track.frozen[start:end]
        #in_left25 = self._track.in_left25[start:end]
        #in_right25 = self._track.in_right25[start:end]
        in_top = self._track.in_top[start:end]
        x = self._track.x[start:end]
        y = self._track.y[start:end]
        numpts = self._track.numpts[start:end]

        # Format nicely
        _format_axis(ax)
        ax.axes.get_yaxis().set_visible(False)

        # Get set axes (specifically, we don't want the y-axis to be autoscaled for us)
        ax.axis([time[0], time[-1], -1.0, 1.0])

        # Mark lost/missing sections
        lost_collection = collections.BrokenBarHCollection.span_where(
            time,
            -1.0, -0.9,
            lost,
            edgecolors='none',
            facecolors='red',
        )
        ax.add_collection(lost_collection)
        missing_collection = collections.BrokenBarHCollection.span_where(
            time,
            -1.0, -0.9,
            missing,
            edgecolors='none',
            facecolors='yellow',
        )
        ax.add_collection(missing_collection)

        # Mark frozen sections
        frozen_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.85, -0.8,
            frozen,
            edgecolors='none',
            facecolors='lightblue',
        )
        ax.add_collection(frozen_collection)

        # Mark in-top sections
        intop_collection = collections.BrokenBarHCollection.span_where(
            time,
            -0.75, -0.7,
            in_top,
            edgecolors='none',
            facecolors='blue',
        )
        ax.add_collection(intop_collection)

#        # Mark in-left25 sections
#        inleft25_collection = collections.BrokenBarHCollection.span_where(
#            time,
#            -0.65, -0.6,
#            in_left25,
#            edgecolors='none',
#            facecolors='purple',
#        )
#        ax.add_collection(inleft25_collection)
#
#        # Mark in-right25 sections
#        inright25_collection = collections.BrokenBarHCollection.span_where(
#            time,
#            -0.65, -0.6,
#            in_right25,
#            edgecolors='none',
#            facecolors='pink',
#        )
#        ax.add_collection(inright25_collection)

        # Plot horizontal position
        ax.plot(time, x*2-1, color='orange', label='x position of fish')

        # Plot height
        ax.plot(time, y*2-1, color='limegreen', label='y position of fish')

        # Plot numpts (scaled so 0 = -1.0 (plot bottom), 20 = 1.0 (top))
        ax.plot(time, -1.0+(numpts/10.0), color='purple', linewidth=1, label='# detected points')

        # Add stick plot of movement (where valid)
#        ax.quiver(
#            time, [0] * len(time),
#            speed*np.cos(theta), speed*np.sin(theta),
#            color=[self._speed2color(s) for s in speed],
#            scale=1,  # scale all to a speed of 1, which should be close to max (tank is 1.0x1.0)
#            scale_units='y',
#            width=0.01,
#            units='inches',
#            headlength=0, headwidth=0, headaxislength=0     # no arrowheads
#        )

        # Add markers/links to debugframes if given
        # Get [tracking]:start_frame for proper offset of debug frame numbers into track data here
        start_frame = int(self._track.config['tracking']['start_frame'])
        for dbgframe in self._dbgframes:
            nameparts = os.path.basename(dbgframe).split('_')
            frameindex = max(0, int(nameparts[1]) - start_frame)  # restrict to index 0 at minimum
            if start <= frameindex < end:
                frametime = self._track.time[frameindex]
                marker = matplotlib.patches.RegularPolygon(  # numVertices=3 -> triangle
                    (frametime, -1.08), numVertices=3, radius=0.08,
                    color='#337AB7',
                    clip_on=False,
                    url='/' + dbgframe
                )
                ax.add_artist(marker)
