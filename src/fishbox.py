#!/usr/bin/env python3

import argparse
import atexit
from collections import OrderedDict
try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser
import logging
import os
import random
import pipes   # TODO: move to python3 and use shlex.quote() instead
import signal
import sys
import threading
import time

import config
import utils
from utils import Phase
from fishbox import experiment


def greedy_parse(s):
    for _type in int, float:
        try:
            return _type(s)
        except:
            pass
    return s


def get_conf(args):
    '''Read a configuration file, add configuration from cmdline args.'''
    config_filename = args.inifile
    if not os.path.isfile(config_filename):
        logging.error("Configuration file not found: %s", config_filename)
        sys.exit(1)

    parser = RawConfigParser()
    parser.read(config_filename)

    conf = {}

    # create a dictionary for each section
    for section in parser.sections():
        conf[section] = {}
        for key in parser.options(section):
            # Currently, all configuration options will be numeric.
            # greedy_parse() converts each to a float or an int, if it can.
            conf[section][key] = greedy_parse(parser.get(section, key))

    # setup a 'general' section of the configuration
    # (mostly for the record in the -setup.txt file)
    conf['general'] = {}
    conf['general']['notes'] = args.notes
    conf['general']['inifile'] = args.inifile
    conf['general']['boxname'] = utils.get_boxname()

    return conf


def setup_phases(args, conf):
    # create a dictionary for relevant cmdline arguments,
    conf['phases'] = {}
    section = conf['phases']
    section['phases_argstrings'] = ' '.join("-p %s" % p for p in args.phases)

    # setup phases data to be used during experiment execution
    phase_args = [p.split(',') for p in args.phases]
    phases = []
    for i, (length, stim, background) in enumerate(phase_args):
        length = int(length)
        # Determine and record whether stimulus is enabled for each phase
        if stim == 'on':
            dostim = True
        elif stim == 'off':
            dostim = False
        elif stim == 'rand':
            dostim = random.choice([True, False])
            logging.info("stim=rand selected for phase %d; chose stimulus %s." % (i, ("ENABLED" if dostim else "DISABLED")))

        phase_data = Phase(i, length, dostim, background)
        phases.append(phase_data)

        section['phase_%d_length' % i] = length
        section['phase_%d_dostim' % i] = dostim
        section['phase_%d_background' % i] = background

    section['phases_data'] = phases


def get_args():
    '''Parse and return command-line arguments.'''
    parser = argparse.ArgumentParser(description='Zebrafish Skinner box experiment.')
    parser.add_argument('id', type=str, nargs='?', default='',
                        help='experiment ID (optional), added to output filenames')
    parser.add_argument('-w', '--watch', action='store_true',
                        help='create a window to see the camera view and tracking information')
    parser.add_argument('--debug-frames', type=int, default=100, metavar='N',
                        help='save an image of the current frame every N frames - also saves a frame any time tracking is lost (default: 100; 0 means no debug frames will be written, including tracking-lost frames)')
    parser.add_argument('--notes', type=str,
                        help='additional notes to be saved alongside the experiment data (optional)')

#    exp_group = parser.add_argument_group('experiment settings')
#    exp_group.add_argument('-t', '--time', type=int, default=None,
#                        help='limit the experiment to TIME minutes (default: run forever / until stopped with CTRL-C)')
#    exp_group.add_argument('--time-from-trigger', action='store_true',
#                        help='when using -t/--time, only start counting the time from the moment the tracking first hits its trigger condition'),
#    stimgroup = exp_group.add_mutually_exclusive_group(required=False)
#    stimgroup.add_argument('--nostim', action='store_true',
#                        help='disable all stimulus for this run')
#    stimgroup.add_argument('--randstim', action='store_true',
#                        help='choose whether to enable or disable stimulus for this run with 50/50 probabilities')
    parser.add_argument('-p', '--phases', type=str, action='append',
                        help='configure phases of the experiment. '
                             'Each phase is specified as "len,stim,background", '
                             'where "len" is the phase length in minutes, '
                             '"stim" is one of '
                             '"on", "off", or "rand", controlling whether the '
                             'stimulus is on, off, or randomly enabled with '
                             'a 50%% chance, '
                             'and "background" is an image file to display on the monitor. '
                             'Specify each phase with its own -p/--phases '
                             'argument in the order the phases should run. '
                             'e.g.: "-p 10,off,a.png -p 30,rand,b.png -p 30,off,a.png" '
                             'If not specified, fishbox runs a single, '
                             'infinite "phase" with stim=True and a black background image.'
                        )

    rare_group = parser.add_argument_group('rarely-used arguments')
    rare_group.add_argument('--inifile', type=str, default='../ini/default.ini',
                            help="path to configuration file specifying physical setup (default: ../ini/default.ini)")
    rare_group.add_argument('--vidfile', type=str,
                            help='read video input from the given file (for testing purposes)')
    rare_group.add_argument('--delay', type=int, default=0,
                            help='delay in ms to add between frames (default: 0) -- useful for slowing video processing/display.')

    return parser.parse_args()


def init_logging(args, conf):
    '''Initialize the logging system.  Uses argdir and id from args, adds 'trackfile' to conf
       as a file object to which track data should be written.'''

    # setup log files
    filetimestamp = time.strftime("%Y%m%d-%H%M%S")
    if args.id:
        name = "%s-%s" % (filetimestamp, args.id)
    else:
        name = filetimestamp
    conf['name'] = name

    # ensure log and image directories exist
    utils.mkdir(config.TRACKDIR)
    debugframe_dir = "%s/%s" % (config.DBGFRAMEDIR, name)
    # Make debugframedir world-writable so rsync can delete it.
    oldmask = os.umask(0)
    utils.mkdir(debugframe_dir)
    os.umask(oldmask)
    conf['debugframe_dir'] = debugframe_dir

    trackfilename = "%s/%s-track.csv" % (config.TRACKDIR, name)
    logfilename = "%s/%s.log" % (config.TRACKDIR, name)

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


def write_setup(conf):
    # Record the setup in a -setup.txt file.

    parser = RawConfigParser(dict_type=OrderedDict)
    for section in conf:
        if not isinstance(conf[section], dict):
            # only record values stored in sections/dicts
            continue

        parser.add_section(section)
        for key in sorted(conf[section]):
            parser.set(section, key, conf[section][key])

    setupfilename = "%s/%s-setup.txt" % (config.TRACKDIR, conf['name'])
    with open(setupfilename, 'w') as setupfile:
        # TODO: move to python3 and use shlex.quote() instead
        cmdline = repr(' '.join(pipes.quote(s) for s in sys.argv))
        setupfile.write("; Command line:\n;    {}\n;\n".format(cmdline))
        setupfile.write("; Configuration:\n")
        parser.write(setupfile)


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
    conf = get_conf(args)
    init_logging(args, conf)

    if args.phases:
        # add phases and runtime-decided config
        setup_phases(args, conf)
        total_time = sum(p.length for p in conf['phases']['phases_data'])
    else:
        # run as a single "infinite" phase with dostim=True
        # and a black background image
        conf['phases'] = {}
        onephase = Phase(0, float('inf'), True, 'black.png')
        conf['phases']['phases_data'] = [onephase]

        total_time = None

    # record all configuration to the setup file
    write_setup(conf)

    # catch SIGINT (ctrl-C) and SIGTERM
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    # setup lock file
    try:
        # O_CREAT | O_EXCL ensure that this call creates the file,
        # raises OSError if file exists
        lockfd = os.open(config.LOCKFILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        lockfile = os.fdopen(lockfd, 'w')
        # store PID, start time (in UTC), and experiment runtime
        lockfile.write("%d\n%d\n%d\n" % (os.getpid(), int(time.time()), total_time*60 if total_time else 0))
        lockfile.close()
        # remove lockfile at exit
        atexit.register(os.unlink, config.LOCKFILE)
    except ValueError:
        logging.error("It appears an experiment is already running (%s exists).  Please wait or end that experiment before starting another." % config.LOCKFILE)
        sys.exit(1)

    # create Experiment object
    exp = experiment.Experiment(conf, args)

    # setup timeout alarm as a backup
    # NOTE: not cross-platform (SIGALRM not available on Windows)
    if total_time and sys.platform in ['cygwin', 'nt']:
        logging.warning("SIGALRM not available under Windows.  Backup timeout not enabled.")
    elif total_time:
        signal.signal(signal.SIGALRM, sighandler)
        signal.alarm(total_time*60 + 60)  # with 60 seconds buffer

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
