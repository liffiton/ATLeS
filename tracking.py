import atexit
import cv2
import logging
import numpy
import os
import subprocess
import sys


class FrameProcessor(object):
    def __init__(self):
        # background subtractor
        #self._bgs = cv2.BackgroundSubtractorMOG()
        #self._bgs = cv2.BackgroundSubtractorMOG2()  # not great defaults, and need bShadowDetection to be False
        #self._bgs = cv2.BackgroundSubtractorMOG(history=10, nmixtures=3, backgroundRatio=0.2, noiseSigma=20)

        # varThreshold: higher values detect fewer/smaller changed regions
        self._bgs = cv2.BackgroundSubtractorMOG2(history=0, varThreshold=3, bShadowDetection=False)

        # ??? history is ignored?  Only if learning_rate is > 0, or...?  Unclear.

        # Learning rate for background subtractor.
        # 0 = never adapts after initial background creation.
        # A bit above 0 looks good.
        # Lower values are better for detecting slower movement, though it
        # takes a bit of time to learn the background initially.
        self._learning_rate = 0.001  # for 10ish fps video?

        # element to reuse in erode/dilate
        # RECT is more robust at removing noise in the erode
        self._element_shrink = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        self._element_grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))

        # contours and centroids for the most recent frame
        self._contours = None
        self._centroids = None

    def process_frame(self, frame, channel=2):
        ''' Process a single frame, using just the given channel.

        Channels:  BGR -> Blue = 0, Green = 1, Red = 2 (default)
        For fishybox: use the red channel (most IR, least visible light)
        '''

        # reset contours and centroids
        self._contours = None
        self._centroids = None

        # grayscale copy
        self._gframe = frame[:,:,channel]

        # subtract background, clean up image
        self._sub_bg()

    def _sub_bg(self):
        mask = self._bgs.apply(self._gframe, learningRate=self._learning_rate)
        self._gframe = self._gframe & mask

        # filter out single pixels
        self._gframe = cv2.erode(self._gframe, self._element_shrink)

        # restore and join nearby regions (in case one fish has a skinny middle...)
        self._gframe = cv2.dilate(self._gframe, self._element_grow)

    def _get_contours(self):
        # find contours
        self._contours, _ = cv2.findContours(self._gframe, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def _get_centroids(self):
        if not self._contours:
            self._get_contours()

        self._centroids = []

        for contour in self._contours:
            moments = cv2.moments(contour)
            if moments['m00'] != 0.0:  # skip zero-area contours
                centroid_x = moments['m10'] / moments['m00']
                centroid_y = moments['m01'] / moments['m00']
                self._centroids.append((centroid_x, centroid_y))

    @property
    def contours(self):
        if not self._contours:
            self._get_contours()

        return self._contours

    @property
    def centroids(self):
        if not self._centroids:
            self._get_centroids()

        return self._centroids


class SimpleTracker(object):
    '''A simple tracking class.  Only ever reports last-known position.  No estimates/predictions.'''
    def __init__(self, w, h):
        self._w = float(w)  # frame width (for scaling coordinates)
        self._h = float(h)  # frame height
        self._pos = numpy.array((None, None))

        self._positions = []

        # How many frames have we not had something to track?
        # Initialized to 100 so status() is initially 'lost'
        self._missing_count = 100

    @property
    def position_pixel(self):
        '''Return the position in pixel coordinates.'''
        return tuple(self._pos)

    def _pixel_to_tank(self, pt):
        '''Transform pixel coordinates to tank coordinates.
        Both x- and y-coordinates are scaled to 0.0-1.0 relative to the view of the tank.
        NOTE: y-axis is inverted from pixel coordinates, so y=0.0 is the **bottom** of the tank.
        '''
        return (pt[0] / self._w, 1.0 - (pt[1] / self._h))

    @property
    def position_tank(self):
        '''Return the position in tank coordinates.
        Both x- and y-coordinates are scaled to 0.0-1.0 relative to the view of the tank.
        NOTE: y-axis is inverted from pixel coordinates, so y=0.0 is the **bottom** of the tank.
        '''
        if self._have_pos:
            return self._pixel_to_tank(self._pos)
        else:
            return self._pos

    @property
    def status(self):
        # is anything currently being tracked
        if not self._have_pos:
            return 'init'
        if self._missing_count == 0:
            return 'acquired'
        elif self._missing_count < 5:
            return 'missing'
        else:
            return 'lost'

    def _score_point(self, pt):
        '''Score a given detection point by its distance from the expected position of the fish.'''
        if self._have_pos:
            expected = self._expected_loc()
            delta = numpy.linalg.norm(expected - pt)
            return delta
        else:
            return 0

    def _get_closest(self, obs):
        if not obs:
            closest = None
        else:
            if len(obs) == 1:
                closest = obs[0]
            else:
                closest = min(obs, key=self._score_point)

            # If we think we have a decent fix, but closest is more than (XXX: magic number!) away,
            # then consider this a bad detection.
            if self.status != 'lost' and self.status != 'init' \
                    and numpy.linalg.norm(closest - self._pos) > (max(self._w, self._h) / 4.0):
                closest = None

        return closest

    def _expected_loc(self):
        # Don't assume anything; just use the last-known position
        return self._pos

    def _update_estimates(self, prevpos):
        # SimpleTracker has no estimates
        pass

    def update(self, obs):
        closest = self._get_closest(obs)

        if self.status == 'acquired':
            # hold on to previous position
            prevpos = self._pos.copy()
        else:
            prevpos = None

        if closest is None:
            # If no good reading, increment missing_count
            self._missing_count += 1
        else:
            # Closest position is new acquired position
            self._missing_count = 0
            self._pos[:] = closest

        self._update_estimates(prevpos)

        if self._have_pos:
            self._positions.append(tuple(int(x) for x in self.position_pixel))

    @property
    def _have_pos(self):
        return not any(x is None for x in self._pos)

    @property
    def positions(self):
        return self._positions


class VelocityTracker(SimpleTracker):
    '''A predictive tracking class.  Estimates position when fish is lost based on recent velocity.'''
    def __init__(self):
        self._vel = numpy.zeros(2)
        super(VelocityTracker, self).__init__()

    def _expected_loc(self):
        return self._pos + self._vel

    def _update_estimates(self, prevpos):
        # self.status is derived from the [just updated] self._missing_count
        if self.status == 'lost':
            # We have no idea where it should be, so no more moving the point.
            self._vel = numpy.zeros(2)
        elif self.status == 'missing':
            # use the expected location
            self._pos = self._expected_loc()
            if numpy.min(self._pos) < 0 or self._pos[0] > self._w or self._pos[1] > self._h:
                # went past the border, so just reset and stop moving
                self._pos -= self._vel
                self._vel = numpy.zeros(2)
            else:
                # taper velocity to zero
                self._vel *= 0.5
        elif self.status == 'acquired':
            # current self._pos is fine, just update estimate velocity if appropriate
            if prevpos is not None:
                # estimated velocity is a [very quickly] decaying average
                alpha = 0.75
                self._vel = alpha * (self._pos - prevpos) + (1-alpha) * self._vel


class Stream(object):
    def __init__(self, source, w=None, h=None, params=None, fps=None, exposure=None):
        if params is None:
            params = {}

        if type(source) == int:
            # webcam
            self._video = self._cam_setup(source, w, h, fps, exposure)
            if self._video is None:
                logging.error("Could not open video stream.")
                sys.exit(1)
            # try to set given parameters
            for key, value in params.items():
                self._video.set(key, value)
                newval = self._video.get(key)
                if newval != value:
                    logging.warning("Unable to set %s to %s, got %s.", key, value, newval)
            self.sourcetype = 'camera'
        elif os.path.isfile(source):
            # video file
            self._video = cv2.VideoCapture(source)
            self.sourcetype = 'file'
        else:
            logging.error("Input file not found: %s", source)
            sys.exit(1)

        if not self._video.isOpened():
            logging.error("Could not open video stream.")
            sys.exit(1)

    def get_video_stats(self):
        assert(self.sourcetype == 'file')

        framecount = self._video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
        fps = self._video.get(cv2.cv.CV_CAP_PROP_FPS)

        return framecount, fps

    @staticmethod
    def _v4l2_call(params):
        try:
            subprocess.call(["v4l2-ctl"] + params.split())
        except OSError:
            logging.warning("Unable to call v4l2-ctl; video stream may not be configured correctly.")

    def _cam_setup(self, source, w, h, fps, exposure):
        try:
            cap = cv2.VideoCapture(source, w, h)
        except TypeError:
            # Don't have our modified version of OpenCV w/ width/height args
            logging.warning("Unmodified OpenCV installation; no width/height control for capture.")
            cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            return None

        # Try setting width/height this way, too, in case we don't have modified OpenCV but this still works.
        cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, h)

        # Read a frame, just in case it's needed before setting params
        rval, _ = cap.read()
        if not rval:
            cap.release()
            return None

        # Hacks using v4l2-ctl to set capture parameters we can't control through OpenCV

        # Set FPS (OpenCV requests 30, hardcoded)
        self._v4l2_call("-p %d" % fps)

        # Turn off white balance (seems to need to be reset to non-zero first, then zero)
        self._v4l2_call("--set-ctrl=white_balance_auto_preset=1")
        self._v4l2_call("--set-ctrl=white_balance_auto_preset=0")

        # Set shutter speed
        # exposure_time_absolute is given in multiples of 0.1ms.
        # Make sure fps above is not set too high (exposure time
        # will be adjusted automatically to allow higher frame rate)
        self._v4l2_call("--set-ctrl=auto_exposure=1")
        self._v4l2_call("--set-ctrl=exposure_time_absolute=%d" % exposure)

        atexit.register(cap.release)

        return cap

    @property
    def width(self):
        return int(self._video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self._video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))

    def get_frame(self):
        rval, frame = self._video.read()
        if not rval:
            return rval, frame
        return rval, frame
