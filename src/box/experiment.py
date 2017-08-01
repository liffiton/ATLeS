import atexit
import collections
import datetime
import logging
import numpy
import os
import time

import cv2

import config

from box import tracking
from box import controllers  # noqa -- 'imported but unused' because used in eval()ed expression
from box import stimulus     # noqa -- ditto
from box import display
from box import wiring

try:
    import sensors
except ImportError:
    sensors = None


class Watcher(object):
    ''' Class for creating, controlling the preview/"--watch" window '''

    RED = (0, 0, 255, 255)
    GREEN = (0, 255, 0, 255)
    BLUE = (255, 0, 0, 255)
    YELLOW = (0, 255, 255, 255)
    STATUS_COLORS = {'acquired': GREEN, 'missing': BLUE, 'lost': RED, 'init': RED}

    def __init__(self, tx1, tx2, ty1, ty2):
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

        # make an image for drawing tank-coord overlays
        tank_overlay = numpy.zeros((ty2-ty1, tx2-tx1, 4), frame.dtype)

        # draw contours
        for c_i in range(len(proc.contours)):
            cv2.drawContours(tank_overlay, proc.contours, c_i, self.GREEN, 1)

        # draw centroids
        for pt in proc.centroids:
            pt = [int(x) for x in pt]
            if pt == track.position_pixel:
                continue  # will draw this one separately
            x = pt[0]
            y = pt[1]
            cv2.line(tank_overlay, (x-5,y), (x+5,y), self.YELLOW)
            cv2.line(tank_overlay, (x,y-5), (x,y+5), self.YELLOW)

        if track.status != 'init':
            # draw a larger cross at the known/estimated position
            color = self.STATUS_COLORS[track.status]
            x,y = track.position_pixel
            cv2.line(tank_overlay, (x-10,y), (x+10,y), color)
            cv2.line(tank_overlay, (x,y-10), (x,y+10), color)

            # draw a circle around the estimated position
            #position = track.position_pixel
            #cv2.circle(tank_overlay, position, 5, self.STATUS_COLORS[track.status])

            # draw a trace of the past k positions recorded
            start = max(0, len(track.positions) - 50)
            prevpt = track.positions[start]
            for pt in track.positions[start:]:
                cv2.line(tank_overlay, prevpt, pt, self.YELLOW)
                prevpt = pt

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

    def __init__(self, conf, args):
        self._conf = conf
        self._args = args

        # Create Sensors
        if sensors is not None:
            self._sensors = sensors.Sensors()
            self._sensors.begin()
        else:
            self._sensors = None
            logging.warn("sensors module not loaded.")

        # Background image manager
        if config.HAS_DISPLAY:
            self._display = display.Display()

        # Evaluate experiment setup expression
        self._control = eval(conf['experiment']['controller'])
        self._stim = eval(conf['experiment']['stimulus'])

        trigger_exp = conf['experiment']['trigger']
        trigger_code = compile(trigger_exp, '<string>', 'eval')

        def _trigger_func(pos_tank):
            xpos, ypos = pos_tank
            return eval(trigger_code)
        self._trigger = _trigger_func

        wiring.IR_on()
        if 'ambient_light_level' in conf['experiment']:
            wiring.visible_on(conf['experiment']['ambient_light_level'])

        # setup Stream (*after* starting stimulus, visible light bar, and IR light bar)
        if args.vidfile:
            self._stream = tracking.Stream(args.vidfile)
            args.width = self._stream.width
            args.height = self._stream.height
        else:
            params = {}
            self._stream = tracking.Stream(0, conf=conf['camera'], params=params)

        # Tank bounds in pixel coordinates
        # NOTE: tank Y coordinate is inverted w.r.t. pixel coordinates, hence (1.0 - ...).
        self._tx1 = int(self._stream.width * self._conf['camera']['tank_min_x'])
        self._tx2 = int(self._stream.width * self._conf['camera']['tank_max_x'])
        self._ty1 = int(self._stream.height * (1.0 - self._conf['camera']['tank_max_y']))
        self._ty2 = int(self._stream.height * (1.0 - self._conf['camera']['tank_min_y']))

        # Vidfile stats, if relevant
        if self._stream.sourcetype == 'file':
            # Get frame count, fps for calculating frame times
            self._framecount, self._fps = self._stream.get_video_stats()
            logging.info("Video file: %d frames, %d fps", self._framecount, self._fps)

        # Tracking: Simple
        tank_width = self._tx2 - self._tx1
        tank_height = self._ty2 - self._ty1
        self._track = tracking.VelocityTracker(w=tank_width, h=tank_height)

        # Frame processing (though these feed into the Tracker, some also rely on its position estimate)
        filt_bgsub = tracking.TargetFilterBGSub()
        filt_bright = tracking.TargetFilterBrightness()
        filt_dist = tracking.TargetFilterDistance(self._track, maxdist=int(tank_width*0.1))
        # First try the AND of both filters' outputs;
        # then the background subtractor alone;
        # then the brightness filter alone but with a distance limit
        #   (brightness should only be needed if fish isn't moving,
        #    so don't accept large jumps from brightness filter)
        self._framefilters = [filt_bgsub & filt_bright, filt_bgsub, filt_bright & filt_dist]
        self._proc = tracking.FrameProcessor()

        # For measuring status percentages
        self._statuses = collections.defaultdict(int)

        # Setup printing stats on exit
        atexit.register(self._print_stats)

        # Record status of previous frame to know when tracking is first lost.
        self._prev_status = None

    def _write_data(self, data, frametime=None):
        '''Write a piece of data to the track file.

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
            frametime = time.time() - self._starttime
        self._conf['trackfile'].write("%0.4f,%s" % (frametime, str(data)))

    def _extract_subframe(self, frame, channel=1):
        ''' Extract the relevant portion of a frame,
        using the configuration's tank bounds and just the given channel.

        Channels:  BGR -> Blue = 0, Green = 1 (default), Red = 2
        For atles_box: use the green channel (all are sensitive to IR, but the
        green appears to be most sensitive channel in general)
        '''
        return frame[self._ty1:self._ty2, self._tx1:self._tx2, channel]

    def _save_debug_frame(self, frame, subframe, frame_num, status, save_full=False):
        ''' Save a copy of the current frame for debugging. '''
        # Save as world-writable so rsync can delete them.
        oldmask = os.umask(0)
        subimgfile = "%s/subframe_%05d_%s.png" % (self._conf['debugframe_dir'], frame_num, status)
        cv2.imwrite(subimgfile, subframe)
        if save_full:
            imgfile = "%s/frame_%05d_%s.png" % (self._conf['debugframe_dir'], frame_num, status)
            cv2.imwrite(imgfile, frame)
        os.umask(oldmask)
        logging.info("Saved frame %d." % frame_num)

    def _apply_filters(self, frame):
        '''Apply our stored filters to the frame, one at at time, until one
        returns a non-empty result.  Return that result.'''
        for filter in self._framefilters:
            output = filter(frame)
            if numpy.any(output):
                return output
        # if we get here, they were all empty, so return the last one (which is empty)
        return output

    def _do_tracking(self, frame, frame_num, phase_data):
        # Process the frame (finds contours, centroids, and updates background subtractor)
        subframe = self._extract_subframe(frame)
        filtered = self._apply_filters(subframe)
        self._proc.new_frame(filtered)

        if frame_num == 1:
            self._save_debug_frame(frame, subframe, frame_num, 'start', save_full=True)

        # Wait for the background subtractor to learn/stabilize
        # before logging or using data.
        if frame_num < self._conf['tracking']['start_frame']:
            return
        elif frame_num == self._conf['tracking']['start_frame']:
            logging.info("Tracking started at frame %d.", frame_num)

        # Update tracker w/ latest set of centroids
        self._track.update(self._proc.centroids)
        # Get the position estimate of the fish and tracking status from the tracker
        # pos_pixel = self._track.position_pixel
        pos_tank = self._track.position_tank
        status = self._track.status

        # Update status counts
        self._statuses[status] += 1

        # Get latest sensor readings
        if self._sensors is not None:
            sensor_vals = self._sensors.get_latest()
        else:
            sensor_vals = {'time': datetime.datetime.now(), 'temp': -1.0, 'lux': -1}

        # Record data
        if pos_tank[0] is None:
            report_pos = ".,."
        else:
            report_pos = "%0.3f,%0.3f" % (pos_tank[0], pos_tank[1])

        data = "%s,%s,%d,%0.2f,%d\n" % (status, report_pos, len(self._proc.centroids), sensor_vals['temp'], sensor_vals['lux'])

        if self._stream.sourcetype == 'file':
            self._write_data(data, frametime=frame_num*1.0/self._fps)
        else:
            self._write_data(data)

        if self._args.debug_frames:
            if status != 'acquired' and self._prev_status == 'acquired':
                # save a frame whenever we first lose tracking (transition from acquired to not)
                self._save_debug_frame(frame, subframe, frame_num, status)
            if frame_num % self._args.debug_frames == 0:
                # save a frame every "debug_frames" frames
                self._save_debug_frame(frame, subframe, frame_num, status)

        if status != 'lost' and status != 'init' and self._trigger(pos_tank):
            # Only provide a stimulus if we know where the fish is
            # and the behavior test for that position says we should.
            if phase_data.dostim:
                self._control.add_hit(str(pos_tank))
                response = self._control.get_response()
                self._stim.show(response)
        else:
            self._stim.show(0)  # 0 = no stimulus

        self._prev_status = status

    def _get_phase_data(self, runningtime):
        t_sum = 0
        for p in self._conf['phases']['phases_data']:
            t_sum += p.length*60
            if runningtime < t_sum:
                return p
        # if we get here, we've run longer than the sum of all phase lengths
        return 'done'

    def run(self):
        self._stim.begin()

        # Create Watcher here because preview window seems to need to be
        # created/managed in same thread under Windows, and this method is
        # run in a different thread than the constructor is.
        if self._args.watch:
            _watcher = Watcher(self._tx1, self._tx2, self._ty1, self._ty2)

        prevtime = time.time()
        frame_num = 0

        self._starttime = time.time()

        phase_data = None

        while True:
            curtime = time.time()

            new_phase_data = self._get_phase_data(curtime-self._starttime)
            if new_phase_data == 'done':
                logging.info("End of last phase reached; exiting.")
                break
            elif new_phase_data != phase_data:
                phase_data = new_phase_data
                logging.info("Starting phase: %s" % (str(phase_data)))
                if config.HAS_DISPLAY:
                    imgfile = str(config.IMGDIR / phase_data.background)
                    self._display.show_image(imgfile)

            stim_msg = self._stim.msg_poll()
            if stim_msg == 'safety limit reached':
                logging.warn("Stimulus safety limit reached; exiting.")
                break
            elif stim_msg == 'quit':
                logging.info("Stimulus window closed; exiting.")
                break

            rval, frame = self._stream.get_frame()

            if not rval:
                logging.warn("stream.get_frame() rval != True")
                break

            frame_num += 1

            self._do_tracking(frame, frame_num, phase_data)

            if self._args.watch:
                _watcher.draw_watch(frame, self._track, self._proc)
                if cv2.waitKey(1) % 256 == 27:
                    logging.info("Escape pressed in preview window; exiting.")
                    break

            # tracking performance / FPS
            if frame_num % 1000 == 0:
                frame_time = (curtime - prevtime) / 1000
                logging.info("%dms / frame : %dfps", 1000*frame_time, 1/frame_time)
                prevtime = curtime

            if self._args.delay:
                time.sleep(self._args.delay / 1000.0)

    def _print_stats(self):
        '''Print status percentages.'''
        total = sum(self._statuses.values())
        logging.info("Status percentages:")
        for status, count in self._statuses.items():
            logging.info("{0:>10}: {1:4.1f}".format(status, 100*count/float(total)))
