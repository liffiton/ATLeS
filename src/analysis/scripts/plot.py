#!/usr/bin/env python3

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

    if args.heat:
        plotter.plot_heatmap(args.heat_num)
    elif args.leftright:
        plotter.plot_leftright()
    else:
        plotter.plot_trace()


show = plot.show

save = plot.savefig
