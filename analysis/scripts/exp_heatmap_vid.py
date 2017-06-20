#!/usr/bin/env python3

import configparser
import glob
import matplotlib.pyplot as plt

from collections import defaultdict

from .. import heatmaps


name = "exp_heatmap_vid"
help = "Generate side-by-side heatmap videos for all left-stimulus tracks and all right-stimulus tracks."


def register_arguments(parser):
    pass


def run(args):
    tracks = defaultdict(list)

    all_setup = glob.glob("data/tracks/*/*LDr*-setup.txt")
    print("Reading data linked to {}...".format(all_setup))
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

    return heatmaps.make_animation(datasets)


show = plt.show

save = None  # use save() method of run() return value
