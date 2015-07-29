import argparse
import atexit
try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser
import logging
import os
import signal
import sys
import threading
import time

import experiment
import tracking


_LOGDIR = "logs/"
_LOCKFILE = _LOGDIR + "explockfile"


def greedy_parse(s):
    for _type in int, float:
        try:
            return _type(s)
        except:
            pass
    return s


def get_conf(config_filename):
    '''Read a configuration file.'''
    if not os.path.isfile(config_filename):
        logging.error("Configuration file not found: %s", config_filename)
        sys.exit(1)

    parser = RawConfigParser()
    parser.read(config_filename)

    conf = {}
    conf['_parserobj'] = parser

    # create a dictionary for each section
    for section in parser.sections():
        conf[section] = {}
        for key in parser.options(section):
            # Currently, all configuration options will be numeric.
            # greedy_parse() converts each to a float or an int, if it can.
            conf[section][key] = greedy_parse(parser.get(section, key))

    return conf


def get_args():
    '''Parse and return command-line arguments.'''
    parser = argparse.ArgumentParser(description='Zebrafish Skinner box experiment.')
    parser.add_argument('id', type=str, nargs='?', default='',
                        help='experiment ID (optional), added to output filenames')
    parser.add_argument('-w', '--watch', action='store_true',
                        help='create a window to see the camera view and tracking information')
    exp_group = parser.add_argument_group('experiment settings')
    exp_group.add_argument('-t', '--time', type=int, default=None,
                        help='limit the experiment to TIME minutes (default: run forever / until stopped with CTRL-C)')
    exp_group.add_argument('--time-from-trigger', action='store_true',
                        help='when using -t/--time, only start counting the time from the moment the tracking first hits its trigger condition'),
    stimgroup = exp_group.add_mutually_exclusive_group(required=False)
    stimgroup.add_argument('--nostim', action='store_true',
                        help='disable all stimulus for this run')
    stimgroup.add_argument('--randstim', action='store_true',
                        help='choose whether to enable or disable stimulus for this run with 50/50 probabilities')

    rare_group = parser.add_argument_group('rarely-used arguments')
    rare_group.add_argument('--inifile', type=str, default='ini/default.ini',
                        help="configuration file specifying physical setup (default: ini/default.ini)")
    rare_group.add_argument('--vidfile', type=str,
                        help='read video input from the given file (for testing purposes)')
    rare_group.add_argument('--delay', type=int, default=0,
                        help='delay in ms to add between frames (default: 0) -- useful for slowing video processing/display.')

    return parser.parse_args()


def init_logging(args, conf):
    '''Initialize the logging system.  Uses argdir and id from args, adds 'trackfile' to conf
       as a file object to which track data should be written.'''

    # ensure log directory exists
    if not os.path.exists(_LOGDIR):
        os.makedirs(_LOGDIR)

    # setup log files
    filetimestamp = time.strftime("%Y%m%d-%H%M%S")
    if args.id:
        name = "%s-%s" % (filetimestamp, args.id)
    else:
        name = filetimestamp
    trackfilename = "%s/%s-track.csv" % (_LOGDIR, name)
    logfilename = "%s/%s.log" % (_LOGDIR, name)

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
    setupfilename = "%s/%s-setup.txt" % (_LOGDIR, name)
    with open(setupfilename, 'w') as setupfile:
        setupfile.write("Command line:\n    %s\n\n" % (' '.join(sys.argv)))
        setupfile.write("Configuration file:\n")
        conf['_parserobj'].write(setupfile)


def sighandler(signum, frame):
    if signum == signal.SIGALRM:
        logging.info("Terminating experiment after timeout.")
        sys.exit(0)
    elif signum == signal.SIGINT:
        logging.info("Caught ctrl-C; exiting.")
        sys.exit(1)
    elif signum == signal.SIGTERM:
        logging.info("Caught SIGTERM; exiting.")
        sys.exit(1)
    else:
        logging.warn("Unexpected signal received (%d); exiting." % signum)
        sys.exit(1)


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
        stream = tracking.Stream(0, conf=conf['camera'], params=params)

    # setup timeout alarm if needed
    # NOTE: not cross-platform (SIGALRM not available on Windows)
    if args.time and sys.platform in ['cygwin', 'nt']:
        logging.error("Timeout not available under Windows.  Timeout option ignored.")
    elif args.time and not args.time_from_trigger:
        signal.signal(signal.SIGALRM, sighandler)
        signal.alarm(args.time*60)

    # catch SIGINT (ctrl-C) and SIGTERM
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    # setup lock file
    try:
        os.open(_LOCKFILE, os.O_CREAT | os.O_EXCL)
        atexit.register(os.unlink, _LOCKFILE)
    except:
        logging.error("It appears an experiment is already running (%s exists).  Please wait or end that experiment before starting another." % _LOCKFILE)
        sys.exit(1)

    exp = experiment.Experiment(conf, args, stream, sighandler)

    # run in separate thread so signal handler is more reliable
    runthread = threading.Thread(target=exp.run)
    runthread.daemon = True       # so thread is killed when main thread exits (e.g. in signal handler)
    runthread.start()
    if sys.version_info[0] >= 3:
        runthread.join()
    else:
        # In Python 2, a timeout is required for join() to not just
        # call a blocking C function (thus blocking the signal handler).
        # However, infinity works.
        runthread.join(float("inf"))

    sys.exit(0)


if __name__ == '__main__':
    main()
