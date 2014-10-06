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
def get_experiment():
    # Controller: Fixed interval or fixed ratio
    #control = controllers.FixedIntervalController(response_interval=3)
    control = controllers.FixedRatioController(1)
    # Control response: static response: constant 1
    control.set_response(1)

    # Stimulus: Visual stimulus or Dummy stimulus (just prints to terminal)
    # Check for whether pygame loaded in stimulus module or not
    if stimulus.pygame is not None:
        stim = stimulus.VisualStimulus()
    else:
        stim = stimulus.DummyStimulus()

    # Behavior test: xpos < 25%
    def behavior_test(pos):
        return pos[0] < 0.25

    return control, stim, behavior_test
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
        fh.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s"))
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(fmt="[%(levelname)s] %(message)s"))
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

    def write_data(self, data, frametime=None):
        '''Write a piece of data to the log file.

        Arguments:
            data: String
                The data to write (preferably a pre-formatted string, but it
                will be converted to a string regardless).
            frametime: Float
                If the input stream is from a file, this can be used to specify
                the time (from the start of the video) of the current frame.
        '''
        if frametime is None:
            # use real time
            frametime = time.time() - self._start
        self._trackfile.write("%0.4f,%s" % (frametime, str(data)))


class Experiment(object):
    RED = (0, 0, 255, 255)
    GREEN = (0, 255, 0, 255)
    BLUE = (255, 0, 0, 255)
    YELLOW = (0, 255, 255, 255)
    STATUS_COLORS = {'acquired': GREEN, 'missing': BLUE, 'lost': RED}

    def __init__(self, conf, args, stream):
        self._conf = conf
        self._args = args
        self._stream = stream
        self._logger = Logger(args.logdir, args.id)
        self._logger.record_setup(args, conf)

        # Experiment setup
        self._control, self._stim, self._behavior_test = get_experiment()

        # Frame processor
        self._proc = tracking.FrameProcessor()

        # Tracking: Simple
        self._track = tracking.SimpleTracker(w=stream.width, h=stream.height, conf=conf['camera'])

        # For mouse interaction
        self._mouse_on = False

    def mouse_callback(self, event, x, y, flags, *args):
        if event == 1:  # mouse down
            self._mouse_on = not self._mouse_on
        self._mousex = x
        self._mousey = y

    def _draw_watch(self, frame, track, proc):
        pos_pixel = track.position_pixel
        status = track.status

        # draw a circle around the estimated position
        position = tuple(int(x) for x in pos_pixel)
        cv2.circle(frame, position, 5, self.STATUS_COLORS[status])

        # draw a red frame around the tank, according to the ini file
        TL = (int(self._stream.width * self._conf['camera']['tank_min_x']),
              int(self._stream.height * self._conf['camera']['tank_min_y']))
        BR = (int(self._stream.width * self._conf['camera']['tank_max_x']),
              int(self._stream.height * self._conf['camera']['tank_max_y']))
        cv2.rectangle(frame, TL, BR, self.RED)

        # draw contours
        #for c_i in range(len(proc.contours)):
        #    cv2.drawContours(frame, proc.contours, c_i, self.GREEN, 1)

        # draw centroids
        for pt in proc.centroids:
            x = int(pt[0])
            y = int(pt[1])
            cv2.line(frame, (x-5,y), (x+5,y), self.YELLOW)
            cv2.line(frame, (x,y-5), (x,y+5), self.YELLOW)

        # draw crosshair and frame coordinates at mouse
        if self._mouse_on:
            cv2.line(frame, (0, self._mousey), (self._stream.width, self._mousey), self.RED)
            cv2.line(frame, (self._mousex, 0), (self._mousex, self._stream.height), self.RED)
            text = "%.3f %.3f" % (float(self._mousex) / self._stream.width, float(self._mousey) / self._stream.height)
            cv2.putText(frame, text, (5, self._stream.height-5), cv2.FONT_HERSHEY_PLAIN, 1, self.RED)

        cv2.imshow("preview", frame)

    def run(self):
        self._stim.begin(self._conf['stimulus'])
        prevtime = time.time()
        curframe = 0

        from_file = self._stream.source == 'file'
        if from_file:
            # Get frame count, fps for calculating frame times
            framecount, fps = self._stream.get_video_stats()

        self._logger.start_time()

        while True:
            stim_msg = self._stim.msg_poll()
            if stim_msg == 'quit':
                logging.info("Stimulus window closed; exiting.")
                break

            rval, frame = self._stream.get_frame()

            if not rval:
                logging.warn("stream.get_frame() rval != True")
                break

            # Process the frame (finds contours, centroids, and updates background subtractor)
            self._proc.process_frame(frame)
            # Update tracker w/ latest set of centroids
            self._track.update(self._proc.centroids)
            # Get the position estimate of the fish and tracking status from the tracker
            # pos_pixel = self._track.position_pixel
            pos_tank = self._track.position_tank
            # pos_frame = self._track.position_frame
            status = self._track.status

            # Record data
            data = "%s,%0.3f,%0.3f\n" % (status, pos_tank[0], pos_tank[1])
            if from_file:
                self._logger.write_data(data, frametime=curframe*1.0/fps)
            else:
                self._logger.write_data(data)

            if self._args.watch:
                self._draw_watch(frame, self._track, self._proc)
                if cv2.waitKey(1) % 256 == 27:
                    logging.info("Escape pressed in preview window; exiting.")
                    break

            if status != 'lost' and self._behavior_test(pos_tank) and not self._args.nostim:
                # Only provide a stimulus if we know where the fish is
                # and the behavior test for that position says we should.
                self._control.add_hit(str(pos_tank))
                response = self._control.get_response()
                if not self._args.nostim:
                    self._stim.show(response)
                else:
                    self._stim.show(None)
            else:
                self._stim.show(None)

            # tracking performance / FPS
            curframe += 1
            if curframe % 100 == 0:
                curtime = time.time()
                frame_time = (curtime - prevtime) / 100
                logging.info("%dms / frame : %dfps" % (1000*frame_time, 1/frame_time))
                prevtime = curtime
