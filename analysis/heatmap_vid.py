#!/usr/bin/env python3

import argparse
import glob
import math

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation
import numpy as np
import pandas


def read_data(wildcard):
    ''' Read all data from the files specified by the given wildcard path.
        Returns a list of dataframes, one per file.
    '''
    colnames = ['time', 'status', 'x', 'y', 'numpts', '_1', '_2']
    paths = glob.glob(wildcard)
    data = []
    for path in paths:
        df = pandas.read_csv(path, header=None, names=colnames, index_col=0)
        data.append(df)
    return data


def plot_heatmap(ax, data, start_time, end_time, nbins):
    ''' Plot a single heatmap on the given axes for given time range across all given dataframes. '''
    ax.clear()
    xpoints = []
    ypoints = []
    for df in data:
        xpoints.extend(df.loc[start_time:end_time]['x'])
        ypoints.extend(df.loc[start_time:end_time]['y'])
    # imshow expects y,x for the image, but x,y for the extents,
    # so we have to manage that here...
    bins = np.concatenate( (np.arange(0,1.0,1.0/nbins), [1.0]) )
    heatmap, yedges, xedges = np.histogram2d(ypoints, xpoints, bins=bins)
    extent = [xedges[0],xedges[-1], yedges[0], yedges[-1]]
    # make sure we always show the full extent of the tank and the full extent of the data,
    # whichever is wider.
    ax.set_xlim(min(0, xedges[0]), max(1, xedges[-1]))
    ax.set_ylim(min(0, yedges[0]), max(1, yedges[-1]))
    norm = Normalize(0, 100)
    return ax.imshow(heatmap, extent=extent, cmap=plt.get_cmap('afmhot'), origin='lower', interpolation='nearest', norm=norm)


def make_animation(data1, data2):
    ''' Create and return a side-by-side heatmap animation for the two given sets of data. '''
    fig, ax = plt.subplots(1, 2)
    maxtime = data1[0].index.max()
    sec_per_frame = 30
    frame_overlap_percent = 200
    frames = math.ceil(maxtime / sec_per_frame)

    def update(frame):
        start_time = (frame*sec_per_frame) % maxtime
        end_time = start_time + sec_per_frame*(frame_overlap_percent/100)
        a = plot_heatmap(ax[0], data1, start_time, end_time, 50)
        b = plot_heatmap(ax[1], data2, start_time, end_time, 50)
        return a, b

    ani = FuncAnimation(fig, update, frames=frames, interval=50, blit=True)
    return ani


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'))
    args = parser.parse_args()

    path1 = '../data/tracks/*/*M*.csv'
    path2 = '../data/tracks/*/*F*.csv'
    print("Reading data from {} and {}...".format(path1, path2))

    males = read_data(path1)
    females = read_data(path2)
    ani = make_animation(males, females)

    if args.outfile:
        print("Saving video to {}...".format(args.outfile.name))
        ani.save(args.outfile.name)
    else:
        plt.show()


if __name__ == '__main__':
    main()
