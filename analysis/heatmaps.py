import math

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas


def read_data(paths):
    ''' Read all data from the files specified by the given list of paths.
        Returns a list of dataframes, one per file.
    '''
    colnames = ['time', 'status', 'x', 'y', 'numpts', '_1', '_2']
    data = []
    for path in paths:
        df = pandas.read_csv(path, header=None, names=colnames, index_col=0)
        data.append(df)
    return data


def get_timeslice(dataframes, start_time, end_time):
    xpoints = []
    ypoints = []
    for df in dataframes:
        xpoints.extend(df.loc[start_time:end_time]['x'])
        ypoints.extend(df.loc[start_time:end_time]['y'])

    return xpoints, ypoints


def plot_heatmap(ax, xpoints, ypoints, nbins, title=None, maxcount=None):
    ''' Plot a single heatmap on the given axes for given time range across all given dataframes. '''
    # imshow expects y,x for the image, but x,y for the extents,
    # so we have to manage that here...
    bins = np.concatenate( (np.arange(0,1.0,1.0/nbins), [1.0]) )
    heatmap, yedges, xedges = np.histogram2d(ypoints, xpoints, bins=bins)
    extent = [xedges[0],xedges[-1], yedges[0], yedges[-1]]
    # make sure we always show the full extent of the tank and the full extent of the data,
    # whichever is wider.
    ax.set_xlim(min(0, xedges[0]), max(1, xedges[-1]))
    ax.set_ylim(min(0, yedges[0]), max(1, yedges[-1]))
    if title:
        ax.set_title(title)
    if maxcount is not None:
        norm = Normalize(0, maxcount)
    else:
        norm = None
    return ax.imshow(heatmap, extent=extent, cmap=plt.get_cmap('afmhot'), origin='lower', interpolation='nearest', norm=norm)


def make_animation(datasets):
    ''' Create and return a side-by-side heatmap animation for the given sets of data.
        Data sets specified as a dictionary with key=title, value=list of dataframes.
    '''
    numplots = len(datasets)
    fig, ax = plt.subplots(1, numplots)

    # get an arbitrary dataset (assuming they're all the same length)
    dataframes = datasets[next(iter(datasets))]
    maxtime = dataframes[0].index.max()
    sec_per_frame = 60
    frame_overlap_percent = 150
    frames = int(math.ceil(maxtime / sec_per_frame))

    nbins = 50

    maxcount = 100

    def update(frame):
        start_time = (frame*sec_per_frame) % maxtime
        end_time = start_time + sec_per_frame*(frame_overlap_percent/100)
        artists = []
        for i, label in enumerate(datasets):
            ax[i].clear()
            x, y = get_timeslice(datasets[label], start_time, end_time)
            artist = plot_heatmap(ax[i], x, y, nbins, title=label, maxcount=maxcount)
            artists.append(artist)
        return artists

    ani = FuncAnimation(fig, update, frames=frames, interval=200, blit=True)
    return ani
