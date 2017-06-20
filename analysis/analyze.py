#!/usr/bin/env python3

import argparse
import numpy as np

import process
import plot


def main():
    parser = argparse.ArgumentParser(description='Analyze zebrafish Skinner box experiment tracks.')
    parser.add_argument('infile', type=str)
    parser.add_argument('outfile', type=str, nargs='?')
    parser.add_argument('-H', '--heat', action='store_true')
    parser.add_argument('--heat-num', type=int, default=1)
    parser.add_argument('-L', '--leftright', action='store_true')
    args = parser.parse_args()

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

    if args.outfile is None:
        plotter.show()
    else:
        plotter.savefig(args.outfile)


if __name__ == '__main__':
    main()
