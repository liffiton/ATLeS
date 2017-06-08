#!/usr/bin/env python3

import argparse
import glob
import matplotlib.pyplot as plt

import heatmaps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'))
    args = parser.parse_args()

    path1 = '../data/tracks/*/*M*.csv'
    path2 = '../data/tracks/*/*F*.csv'
    print("Reading data from {} and {}...".format(path1, path2))

    paths1 = glob.glob(path1)
    paths2 = glob.glob(path2)

    datasets = {}
    datasets['Male'] = heatmaps.read_data(paths1)
    datasets['Female'] = heatmaps.read_data(paths2)

    ani = heatmaps.make_animation(datasets)

    if args.outfile:
        print("Saving video to {}...".format(args.outfile.name))
        ani.save(args.outfile.name)
    else:
        plt.show()


if __name__ == '__main__':
    main()
