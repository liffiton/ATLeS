import atexit
import collections
import logging
import numpy
import os
import sys
import time

import cv2

import tracking
import controllers
import stimulus

try:
    import sensors
except:
    sensors = None


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
        fh.setFormatter(
            logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s"))
        sh = logging.StreamHandler()
        sh.setFormatter(
            logging.Formatter(fmt="[%(levelname)s] %(message)s"))
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


class Watcher(object):
    ''' Class for creating, controlling the preview/"--watch" window '''

    RED = (0, 0, 255, 255)
    GREEN = (0, 255, 0, 255)
    BLUE = (255, 0, 0, 255)
    YELLOW = (0, 255, 255, 255)
    STATUS_COLORS = {'acquired': GREEN, 'missing': BLUE, 'lost': RED}

    def __init__(self, tx1, tx2, ty1, ty2, tracking):
        # For mouse interaction
        self._mouse_on = False
        cv2.namedWindow("preview")
        atexit.register(cv2.destroyAllWindows)
        cv2.setMouseCallback("preview", self.mouse_callback)
        # Setup tank bounds
        self._tx1 = tx1
        self._tx2 = tx2
        self._ty1 = ty1
        self._ty2 = ty2
        # Record whether we have any tracking to display
        self._tracking = tracking

    def mouse_callback(self, event, x, y, flags, *args):
        if event == 1:  # mouse down
            self._mouse_on = not self._mouse_on
        self._mousex = x
        self._mousey = y

    def draw_watch(self, frame, track, proc):
        tx1 = self._tx1
        tx2 = self._tx2
        ty1 = self._ty1
        ty2 = self._ty2

        # draw a red frame around the tank, according to the ini file
        TL = (tx1, ty1)
        BR = (tx2, ty2)
        cv2.rectangle(frame, TL, BR, self.RED)

        if self._tracking:
            # make an image for drawing tank-coord overlays
            tank_overlay = numpy.zeros((ty2-ty1, tx2-tx1, 4), frame.dtype)

            # draw contours
            for c_i in range(len(proc.contours)):
                cv2.drawContours(tank_overlay, proc.contours, c_i, self.GREEN, 1)

            # draw centroids
            for pt in proc.centroids:
                if pt == track.position_pixel:
                    continue  # will draw this one separately
                x = int(pt[0])
                y = int(pt[1])
                cv2.line(tank_overlay, (x-5,y), (x+5,y), self.YELLOW)
                cv2.line(tank_overlay, (x,y-5), (x,y+5), self.YELLOW)

            # draw a cross at the known/estimated position
            color = self.STATUS_COLORS[track.status]
            x,y = tuple(int(x) for x in track.position_pixel)
            cv2.line(tank_overlay, (x-5,y), (x+5,y), color)
            cv2.line(tank_overlay, (x,y-5), (x,y+5), color)

            # draw a circle around the estimated position
            #position = tuple(int(x) for x in track.position_pixel)
            #cv2.circle(tank_overlay, position, 5, self.STATUS_COLORS[track.status])

            # draw the overlay into the frame at the tank's location
            alpha = tank_overlay[:,:,3]
            for c in 0,1,2:
                frame[ty1:ty2,tx1:tx2,c] = frame[ty1:ty2,tx1:tx2,c]*(1-alpha/255.0) + tank_overlay[:,:,c]*(alpha/255.0)

        # draw crosshair and frame coordinates at mouse
        if self._mouse_on:
            height, width = frame.shape[:2]
            cv2.line(frame, (0, self._mousey), (width, self._mousey), self.RED)
            cv2.line(frame, (self._mousex, 0), (self._mousex, height), self.RED)
            # NOTE: tank Y coordinate is inverted: 0=bottom, 1=top of frame.
            text = "%.3f %.3f" % (float(self._mousex) / width, 1.0 - (float(self._mousey) / height))
            cv2.putText(frame, text, (5, height-5), cv2.FONT_HERSHEY_PLAIN, 1, self.RED)

        cv2.imshow("preview", frame)


class Experiment(object):

    def __init__(self, conf, args, stream):
        self._conf = conf
        self._args = args
        self._stream = stream
        self._logger = Logger(args.logdir, args.id)
        self._logger.record_setup(args, conf)

        # Tank bounds in pixel coordinates
        # NOTE: tank Y coordinate is inverted w.r.t. pixel coordinates, hence (1.0 - ...).
        self._tx1 = int(self._stream.width * self._conf['camera']['tank_min_x'])
        self._tx2 = int(self._stream.width * self._conf['camera']['tank_max_x'])
        self._ty1 = int(self._stream.height * (1.0 - self._conf['camera']['tank_max_y']))
        self._ty2 = int(self._stream.height * (1.0 - self._conf['camera']['tank_min_y']))

        # Create Watcher
        if self._args.watch:
            self._watcher = Watcher(self._tx1, self._tx2, self._ty1, self._ty2, not self._args.notrack)

        # Create Sensors
        if sensors is not None:
            self._sensors = sensors.Sensors()
            self._sensors.begin()
        else:
            logging.warn("sensors module not loaded")

        # Experiment setup
        self._control, self._stim, self._behavior_test = get_experiment()

        if not self._args.notrack:
            # Frame processor
            self._proc = tracking.FrameProcessor()

            # Tracking: Simple
            tank_width = self._tx2 - self._tx1
            tank_height = self._ty2 - self._ty1
            self._track = tracking.SimpleTracker(w=tank_width, h=tank_height)

            # For measuring status percentages
            self._statuses = collections.defaultdict(int)

            # Setup printing stats on exit
            atexit.register(self._print_stats)
        else:
            self._proc = None
            self._track = None

    def run(self):
        self._stim.begin(self._conf['stimulus'])
        prevtime = time.time()
        curframe = 0

        from_file = self._stream.source == 'file'
        if from_file:
            # Get frame count, fps for calculating frame times
            framecount, fps = self._stream.get_video_stats()
            logging.info("Video file: %d frames, %d fps" % (framecount, fps))

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

            curframe += 1

            if not self._args.notrack:
                # Process the frame (finds contours, centroids, and updates background subtractor)
                tank_crop = frame[self._ty1:self._ty2,self._tx1:self._tx2,:]
                self._proc.process_frame(tank_crop)

                # Wait for the background subtractor to learn/stabilize
                # before logging or using data.
                if curframe < self._args.start_frame:
                    continue
                elif curframe == self._args.start_frame:
                    logging.info("Tracking started.")

                # Update tracker w/ latest set of centroids
                self._track.update(self._proc.centroids)
                # Get the position estimate of the fish and tracking status from the tracker
                # pos_pixel = self._track.position_pixel
                pos_tank = self._track.position_tank
                status = self._track.status

                # Update status counts
                self._statuses[status] += 1

                # Get latest sensor readings
                if sensors is not None:
                    sensor_vals = self._sensors.get_latest()
                else:
                    sensor_vals = {'temp': -1.0, 'lux': -1}

                # Record data
                data = "%s,%0.3f,%0.3f,%d,%0.2f,%d\n" % (status, pos_tank[0], pos_tank[1], len(self._proc.centroids), sensor_vals['temp'], sensor_vals['lux'])
                if from_file:
                    self._logger.write_data(data, frametime=curframe*1.0/fps)
                else:
                    self._logger.write_data(data)

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

            if self._args.watch:
                self._watcher.draw_watch(frame, self._track, self._proc)
                if cv2.waitKey(1) % 256 == 27:
                    logging.info("Escape pressed in preview window; exiting.")
                    break

            # tracking performance / FPS
            if curframe % 100 == 0:
                curtime = time.time()
                frame_time = (curtime - prevtime) / 100
                logging.info("%dms / frame : %dfps" % (1000*frame_time, 1/frame_time))
                prevtime = curtime

            if self._args.delay:
                time.sleep(self._args.delay / 1000.0)

    def _print_stats(self):
        '''Print status percentages.'''
        total = sum(self._statuses.values())
        logging.info("Status percentages:")
        for status, count in self._statuses.items():
            logging.info("{0:>10}: {1:4.1f}".format(status, 100*count/float(total)))
