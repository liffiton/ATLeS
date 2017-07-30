import glob
import matplotlib.pyplot as plt

from .. import heatmaps


name = "mf_heatmap_vid"
help = "Generate side-by-side heatmap videos for all male tracks and all female tracks."


def register_arguments(parser):
    pass


def run(args):
    path1 = 'data/tracks/*/*M*.csv'
    path2 = 'data/tracks/*/*F*.csv'
    print("Reading data from {} and {}...".format(path1, path2))

    paths1 = glob.glob(path1)
    paths2 = glob.glob(path2)

    datasets = {}
    datasets['Male'] = heatmaps.read_data(paths1)
    datasets['Female'] = heatmaps.read_data(paths2)

    return heatmaps.make_animation(datasets)


show = plt.show

save = None  # use save() method of run() return value
