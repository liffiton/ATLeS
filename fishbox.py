import argparse
import ConfigParser
import logging
import os
import signal
import sys
import time

import experiment
import tracking


def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


def get_conf(config_filename):
    '''Read a configuration file.'''
    if not os.path.isfile(config_filename):
        logging.error("Configuration file not found: %s", config_filename)
        sys.exit(1)

    parser = ConfigParser.RawConfigParser()
    parser.read(config_filename)

    conf = {}
    conf['_parserobj'] = parser

    # create a dictionary for each section
    for section in parser.sections():
        conf[section] = {}
        for key in parser.options(section):
            # Currently, all configuration options will be numeric.
            # num() converts each to a float or an int, as appropriate.
            conf[section][key] = num(parser.get(section, key))

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
    parser.add_argument('--notrack', action='store_true',
                        help='disable all tracking for this run (implies --nostim; useful for checking/aligning camera)')
    # TODO: separate frequent/useful arguments from infrequest/testing arguments (below
    parser.add_argument('--inifile', type=str, default='default.ini',
                        help="configuration file specifying physical setup (default: default.ini)")
    parser.add_argument('-w', '--watch', action='store_true',
                        help='create a window to see the camera view and tracking information')
    parser.add_argument('-W', '--width', type=int, default=192,
                        help='video capture resolution width (default: 192)')
    parser.add_argument('-H', '--height', type=int, default=144,
                        help='video capture resolution height (default: 144)')
    parser.add_argument('--logdir', type=str, default='./logs',
                        help='directory for storing log/data files (default: ./logs)')
    parser.add_argument('--fps', type=int, default=10,
                        help='video capture frames per second (default: 10) -- also affects rate of stimulus blinking and behavior/position tests.')
    parser.add_argument('--exposure', type=int, default=200,
                        help='video capture exposure time, given in multiples of 0.1ms (default: 200)')
    parser.add_argument('--vidfile', type=str,
                        help='read video input from the given file (for testing purposes)')
    parser.add_argument('--delay', type=int, default=0,
                        help='delay in ms to add between frames (default: 0) -- useful for slowing video processing/display.')
    parser.add_argument('--start-frame', type=int, default=300,
                        help='start tracking at a given frame number (default: 300) -- allow the background learner to stabilize and/or to view a particular position in a video for testing.')

    return parser.parse_args()


def init_logging(args, conf):
    '''Initialize the logging system.  Uses argdir and id from args, adds 'trackfile' to conf
       as a file object to which track data should be written.'''

    # ensure log directory exists
    if not os.path.exists(args.logdir):
        os.makedirs(args.logdir)

    # setup log files
    filetimestamp = time.strftime("%Y%m%d-%H%M%S")
    if args.id:
        name = "%s-%s" % (filetimestamp, args.id)
    else:
        name = filetimestamp
    trackfilename = "%s/%s-track.csv" % (args.logdir, name)
    logfilename = "%s/%s.log" % (args.logdir, name)

    # Setup the ROOT level logger to send to a log file and console both
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(filename=logfilename)
    fh.setFormatter(
        logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s"))
    sh = logging.StreamHandler()
    sh.setFormatter(
        logging.Formatter(fmt="[%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(sh)

    logging.info("Logging started.")

    conf['trackfile'] = open(trackfilename, 'w')

    # Record the setup in a -setup.txt file.
    setupfilename = "%s/%s-setup.txt" % (args.logdir, name)
    with open(setupfilename, 'w') as setupfile:
        setupfile.write("Command line:\n    %s\n\n" % (' '.join(sys.argv)))
        setupfile.write("Configuration file:\n")
        conf['_parserobj'].write(setupfile)


def sig_handler(signum, frame):
    if signum == signal.SIGALRM:
        logging.info("Terminating experiment after timeout.")
    elif signum == signal.SIGINT:
        logging.info("Caught ctrl-C; exiting.")

    sys.exit(0)


def main():
    args = get_args()
    conf = get_conf(args.inifile)
    init_logging(args, conf)

    if args.vidfile:
        stream = tracking.Stream(args.vidfile)
        args.width = stream.width
        args.height = stream.height
    else:
        params = {}
        stream = tracking.Stream(0, w=args.width, h=args.height, params=params, fps=args.fps, exposure=args.exposure)

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
