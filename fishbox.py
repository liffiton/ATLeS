import argparse
import atexit
import ConfigParser
import logging
import signal
import sys

import cv2

import experiment
import tracking


def get_conf():
    '''Read a configuration file, if present, else use default values.'''
    stim_defaults = {
        'x': 0,
        'y': 0,
        'width': 640,
        'height': 480
    }
    parser = ConfigParser.RawConfigParser()
    parser.read('default.ini')

    conf = {}
    conf['_parserobj'] = parser
    conf['stimulus'] = {}
    for key in stim_defaults:
        conf['stimulus'][key] = stim_defaults[key]
    for key in parser.options('stimulus'):
        conf['stimulus'][key] = parser.getint('stimulus', key)

    return conf


def get_args():
    '''Parse and return command-line arguments.'''
    parser = argparse.ArgumentParser(description='Zebrafish Skinner box experiment.')
    parser.add_argument('id', type=str, nargs='?', default='',
                        help='experiment ID (optional), added to output filenames')
    parser.add_argument('-t', '--time', type=int, default=None,
                        help='limit the experiment to TIME minutes (default: run forever / until stopped with CTRL-C)')
    parser.add_argument('--nostim', action='store_true',
                        help='disable all stimulus for this run')
    # TODO: separate frequent/useful arguments from infrequest/testing arguments (below
    parser.add_argument('-w', '--watch', action='store_true',
                        help='create a window to see the camera view and tracking information')
    parser.add_argument('-W', '--width', type=int, default=160,
                        help='video capture resolution width (default: 160)')
    parser.add_argument('-H', '--height', type=int, default=120,
                        help='video capture resolution height (default: 120)')
    parser.add_argument('--logdir', type=str, default='./logs',
                        help='directory for storing log/data files (default: ./logs)')
    parser.add_argument('--fps', type=int, default=5,
                        help='video capture frames per second (default: 5) -- also affects rate of stimulus blinking and behavior/position tests.')
    parser.add_argument('--vidfile', type=str,
                        help='read video input from the given file (for testing purposes)')

    return parser.parse_args()


def sig_handler(signum, frame):
    if signum == signal.SIGALRM:
        logging.info("Terminating experiment after timeout.")
    elif signum == signal.SIGINT:
        logging.info("Caught ctrl-C; exiting.")

    sys.exit(0)


def main():
    conf = get_conf()
    args = get_args()

    if args.vidfile:
        stream = tracking.Stream(args.vidfile)
    else:
        params = {}
        # NOTE: requires my hacked version of OpenCV w/ width/height constructor
        stream = tracking.Stream(0, w=args.width, h=args.height, params=params, fps=args.fps)

    if args.watch:
        cv2.namedWindow("preview")
        atexit.register(cv2.destroyAllWindows)

    # setup timeout alarm if needed
    # NOTE: not cross-platform (SIGALRM not available on Windows)
    if args.time:
        signal.signal(signal.SIGALRM, sig_handler)
        signal.alarm(args.time*60)

    # catch SIGINT (ctrl-C)
    signal.signal(signal.SIGINT, sig_handler)

    exp = experiment.Experiment(conf, args, stream)
    exp.run()

    sys.exit(0)


if __name__ == '__main__':
    main()
