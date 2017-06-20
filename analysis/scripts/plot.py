#!/usr/bin/env python3

import numpy as np

from .. import process, plot

name = "plot"
help = "Generate a plot for a single track."


def register_arguments(parser):
    parser.add_argument('infile', type=str)
    parser.add_argument('-H', '--heat', action='store_true')
    parser.add_argument('--heat-num', type=int, default=1)
    parser.add_argument('-L', '--leftright', action='store_true')


def run(args):
    ''' The default command.  Creates and shows or saves a single plot. '''
    processor = process.TrackProcessor(args.infile)
    plotter = plot.TrackPlotter(processor)

    stats = processor.get_stats()
    maxlen = max(len(key) for key in stats.keys())
    for key, val in stats.items():
        if type(val) is np.float32 or type(val) is np.float64:
            val = "%0.3f" % val
        print("%*s: %s" % (maxlen, key, str(val)))

    if args.heat:
        plotter.plot_heatmap(args.heat_num)
    elif args.leftright:
        plotter.plot_leftright()
    else:
        plotter.plot_trace()


show = plot.show

save = plot.savefig
