import logging
import os
import sys
import time

import cv2

import tracking
import controllers
import stimulus

#############################################################
# Experiment setup (controller, stimulus, and test)

# Controller: Fixed interval or fixed ratio
#control = controllers.FixedIntervalController(response_interval=3)
control = controllers.FixedRatioController(1)
# Conrol response: static response at position (100,100)
control.set_response(100)

# Stimulus: Visual stimulus or Dummy stimulus (just prints to terminal)
stim = stimulus.VisualStimulus()
#stim = stimulus.DummyStimulus()

# Log directory
logdir = "./logs"


# Behavior test: xpos > 10
def behavior_test(pos):
    return pos[0] > 10
#
####################################################################


class Logger(object):
    def __init__(self, logdir, expid=None):
        self._dir = logdir
        self._id = expid

        # ensure log directory exists
        if not os.path.exists(self._dir):
            os.makedirs(self._dir)

        # setup log files
        filetimestamp = time.strftime("%Y%m%d-%H%M")
        if self._id:
            self._name = "%s-%s" % (filetimestamp, self._id)
        else:
            self._name = filetimestamp
        self._trackfilename = "%s/%s-track.csv" % (self._dir, self._name)
        self._logfilename = "%s/%s.log" % (self._dir, self._name)

        # Setup the ROOT level logger to send to a log file and console both
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(filename=self._logfilename)
        fh.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s:%(message)s"))
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(fmt="%(levelname)s:%(message)s"))
        logger.addHandler(fh)
        logger.addHandler(sh)

        logging.info("Logging started.")

        self._trackfile = open(self._trackfilename, 'w')

    def record_setup(self, args, conf):
        setupfilename = "%s/%s-setup.txt" % (self._dir, self._name)
        with open(setupfilename, 'w') as setupfile:
            setupfile.write("Command line:\n    %s\n\n" % (' '.join(sys.argv)))
            setupfile.write("Configuration file:\n")
            conf['_parserobj'].write(setupfile)

    def start_time(self):
        self._start = time.time()

    def write_data(self, data):
        self._trackfile.write("%0.4f,%s" % (time.time()-self._start, data))


class Experiment(object):
    def __init__(self, conf, args, stream):
        self._conf = conf
        self._args = args
        self._stream = stream
        self._logger = Logger(args.logdir, args.id)
        self._logger.record_setup(args, conf)

        # Frame processor
        self._proc = tracking.FrameProcessor()

        # Tracking: Simple
        self._track = tracking.SimpleTracker(w=args.width, h=args.height, conf=conf['camera'])

    def run(self):
        stim.begin(self._conf['stimulus'])
        prevtime = time.time()
        frames = 0

        self._logger.start_time()

        while True:
            stim.blank()
            rval, frame = self._stream.get_frame()
            stim.unblank()

            if not rval:
                break

            # Process the frame (finds contours, centroids, and updates background subtractor)
            self._proc.process_frame(frame)
            # Update tracker w/ latest set of centroids
            self._track.update(self._proc.centroids)
            # Get the position estimate of the fish and tracking status from the tracker
            pos_pixel = self._track.position_pixel
            pos_frame = self._track.position_frame
            pos_tank = self._track.position_tank
            status = self._track.status

            # Record data
            self._logger.write_data("%s,%0.3f,%0.3f\n" % (status, pos_frame[0], pos_frame[1]))

            if self._args.watch:
                # draw a green circle around the estimated position
                position = tuple(int(x) for x in pos_pixel)
                cv2.circle(frame, position, 5, (0,255,0,255))
                # draw a red frame around the tank, according to the ini file
                TL = (int(self._args.width * self._conf['camera']['tank_min_x']),
                      int(self._args.height * self._conf['camera']['tank_min_y']))
                BR = (int(self._args.width * self._conf['camera']['tank_max_x']),
                      int(self._args.height * self._conf['camera']['tank_max_y']))
                cv2.rectangle(frame, TL, BR, (0,0,255,255))
                cv2.imshow("preview", frame)
                if cv2.waitKey(1) % 256 == 27:
                    break

            if behavior_test(pos_tank):
                control.add_hit(str(pos_tank))
                response = control.get_response()
                if not self._args.nostim:
                    stim.show(response)
                else:
                    stim.show(None)
            else:
                stim.show(None)

            # tracking performance / FPS
            frames += 1
            if frames % 10 == 0:
                curtime = time.time()
                frame_time = (curtime - prevtime) / 10
                print("%dms: %dfps" % (1000*frame_time, 1/frame_time))
                prevtime = curtime
