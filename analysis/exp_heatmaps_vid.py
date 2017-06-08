#!/usr/bin/env python3

import argparse
import configparser
import glob
import matplotlib.pyplot as plt

from collections import defaultdict

import heatmaps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'))
    args = parser.parse_args()

    tracks = defaultdict(list)

    all_setup = glob.glob("../data/tracks/*/*LDr*-setup.txt")
    for setupfile in all_setup:
        config = configparser.ConfigParser()
        config.read(setupfile)
        stim = config['experiment']['stimulus']
        trig = config['experiment']['trigger']

        #key = stim + "|" + trig
        if " stim_level=0" in stim:
            key = "darkstim"
        else:
            key = "lightstim"
        if ">" in trig:
            key += "-right"
        else:
            key += "-left"

        trackfile = setupfile.replace('-setup.txt', '-track.csv')

        tracks[key].append(trackfile)

    datasets = defaultdict(list)
    for label, paths in tracks.items():
        data = heatmaps.read_data(paths)
        # "flip" right stimulus to be combined with left stimulus
        if "right" in label:
            label = label.replace("right", "left")
            for df in data:
                df['x'] = 1 - df['x']
        datasets[label].extend(data)

    ani = heatmaps.make_animation(datasets)

    if args.outfile:
        print("Saving video to {}...".format(args.outfile.name))
        ani.save(args.outfile.name)
    else:
        plt.show()


if __name__ == '__main__':
    main()
