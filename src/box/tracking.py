import atexit
import cv2
import logging
import numpy
import os
import subprocess
import sys


class TargetFilterBase(object):
    def __init__(self):
        self._cache = (None, None)

    def __call__(self, frame):
        '''Simple caching around a _do_filter method defined in subclasses.'''
        if frame is self._cache[0]:
            return self._cache[1]

        # apply filter to a copy of the frame's data, as it may modify it
        filtered = self._do_filter(frame[:])
        self._cache = (frame, filtered)
        return filtered

    def __and__(self, other):
        '''Return a callable that produces the Boolean AND of the
        filtered frames produced by calling self and other on the input.'''
        def filter_frame(frame):
            return self(frame) & other(frame)

        return filter_frame

    def __or__(self, other):
        '''Return a callable that produces the Boolean OR of the
        filtered frames produced by calling self and other on the input.'''
        def filter_frame(frame):
            return self(frame) | other(frame)

        return filter_frame


class TargetFilterDistance(TargetFilterBase):
    ''' The Distance filter just returns a filled circle around the last position
    estimate from its tracker object.  This should not be used by itself but rather
    combined with another filter to limit the distance from the last estimate that
    it will "consider."
    '''
    def __init__(self, tracker, maxdist):
        super(TargetFilterDistance, self).__init__()

        self._tracker = tracker
        self._maxdist = maxdist

    def _do_filter(self, frame):
        ''' "Process" (really "draw" in this case) a single frame. '''
        pos = self._tracker.position_pixel
        if any(x is None for x in pos):
            # no position, so return a filled frame (any position is okay)
            ret = numpy.ones_like(frame)
        else:
            # black w/ white circle around position estimate
            ret = numpy.zeros_like(frame)
            cv2.circle(ret, pos, self._maxdist, color=(255,255,255), thickness=-1)  # thickness=-1 -> filled circle

        return ret


class TargetFilterBrightness(TargetFilterBase):
    def __init__(self):
        super(TargetFilterBrightness, self).__init__()

        # elements to reuse in erode/dilate
        # CROSS elimates more horizontal/vertical lines and leaves more
        # blobs with extent in both axes [than RECT].
        self._element_shrink = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
        self._element_grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))

    def _do_filter(self, frame):
        ''' Process a single frame. '''
        # blur to reduce noise
        frame = cv2.GaussianBlur(frame, (5, 5), 0, borderType=cv2.BORDER_CONSTANT)

        # threshold to find contiguous regions of "bright" pixels
        # ignore all "dark" (<1/8 max) pixels
        max = numpy.max(frame)
        min = numpy.min(frame)
        # if the frame is completely dark, then just return it
        if max == min:
            return frame
        threshold = min + (max - min) / 8
        _, frame = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)

        # filter out single pixels and other noise
        frame = cv2.erode(frame, self._element_shrink)

        # restore and join nearby regions (in case one fish has a skinny middle...)
        frame = cv2.dilate(frame, self._element_grow)

        return frame


class TargetFilterBGSub(TargetFilterBase):
    def __init__(self):
        super(TargetFilterBGSub, self).__init__()

        # background subtractor
        #self._bgs = cv2.BackgroundSubtractorMOG()
        #self._bgs = cv2.BackgroundSubtractorMOG2()  # not great defaults, and need bShadowDetection to be False
        #self._bgs = cv2.BackgroundSubtractorMOG(history=10, nmixtures=3, backgroundRatio=0.2, noiseSigma=20)

        # varThreshold: higher values detect fewer/smaller changed regions
        self._bgs = cv2.createBackgroundSubtractorMOG2(history=0, varThreshold=8, detectShadows=False)

        # ??? history is ignored?  Only if learning_rate is > 0, or...?  Unclear.

        # Learning rate for background subtractor.
        # 0 = never adapts after initial background creation.
        # A bit above 0 looks good.
        # Lower values are better for detecting slower movement, though it
        # takes a bit of time to learn the background initially.
        self._learning_rate = 0.001

        # elements to reuse in erode/dilate
        # CROSS elimates more horizontal/vertical lines and leaves more
        # blobs with extent in both axes [than RECT].
        self._element_shrink = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
        self._element_grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))

    def _do_filter(self, frame):
        ''' Process a single frame. '''
        # subtract background, clean up image
        mask = self._bgs.apply(frame, learningRate=self._learning_rate)

        # filter out single pixels
        mask = cv2.erode(mask, self._element_shrink)

        # restore and join nearby regions (in case one fish has a skinny middle...)
        mask = cv2.dilate(mask, self._element_grow)

        return mask


class FrameProcessor(object):
    def __init__(self):
        # most recent frame and its contours and centroids
        self._frame = None
        self._contours = None
        self._centroids = None

    def new_frame(self, frame):
        self._frame = frame
        # reset contours and centroids
        self._contours = None
        self._centroids = None

    def _get_contours(self):
        # find contours
        _, self._contours, _ = cv2.findContours(self._frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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


class TrackerBase(object):
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
        '''Return the position in integer pixel coordinates.'''
        if self._have_pos():
            return tuple(int(x) for x in self._pos)
        else:
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
        if self._have_pos():
            return self._pixel_to_tank(self._pos)
        else:
            return self._pos

    def _have_pos(self):
        return not any(x is None for x in self._pos)

    @property
    def positions(self):
        return self._positions

    def _get_closest(self, obs):
        if not obs:
            return None
        else:
            scored = [(self._score_point(pt), pt) for pt in obs]
            closest = max(scored)

            if closest[0] < 0:
                return None

            return closest[1]

    @property
    def status(self):
        # is anything currently being tracked
        if not self._have_pos():
            return 'init'
        if self._missing_count == 0:
            return 'acquired'
        elif self._missing_count < 5:
            return 'missing'
        else:
            return 'lost'

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

        if self._have_pos():
            self._positions.append(self.position_pixel)


class SimpleTracker(TrackerBase):
    '''A simple tracking class.  Only ever reports last-known position.  No
    estimates/predictions.
    '''
    def _score_point(self, pt):
        '''Score a given detection point by its distance from the last known
        position of the fish.

        Returns:
            A floating point value between 0 and 1 indicating a score (1 is
            highest/best score) or -1 if the point is determined to be invalid.
        '''
        if self._have_pos():
            expected = self._pos
            dist = numpy.linalg.norm(expected - pt)

            # If closest is farther away than we estimate the fish could be
            # (based on fish's max velocity and number of tracking-missing
            # frames) then consider this a bad detection.
            # NOTE: based on a semi-magic number: max_dist_per_frame...
            max_dist_per_frame = 0.2 * self._w  # assume fish can't move more than 20% of tank in one frame time
            max_est_dist = (self._missing_count + 1) * max_dist_per_frame
            if dist > max_est_dist:
                # not considered a valid point
                return -1

            # scale (dist==0)->1.0, (dist==inf)->0.0
            score = 1.0 / (dist+1)
            return score
        else:
            # as good as any other, if we have no idea where the fish is to start
            return 0

    def _update_estimates(self, prevpos):
        # SimpleTracker has no estimates
        pass


class VelocityTracker(TrackerBase):
    '''A predictive tracking class.  Estimates position when fish is lost based on recent velocity.'''
    def __init__(self, w, h):
        super(VelocityTracker, self).__init__(w, h)
        self._vel = numpy.zeros(2)

    def _score_point(self, pt):
        '''Score a given detection point by its distance from the last known
        position of the fish.

        Returns:
            A floating point value between 0 and 1 indicating a score (1 is
            highest/best score) or -1 if the point is determined to be invalid.
        '''
        if self._have_pos():
            # expect it continues moving with some fraction
            # of its previous velocity
            expected = self._pos + self._vel * 0.5
            dist = numpy.linalg.norm(expected - pt)

            # If closest is farther away than we estimate the fish could be
            # (based on fish's max velocity and number of tracking-missing
            # frames) then consider this a bad detection.
            # NOTE: based on a semi-magic number: max_dist_per_frame...
            max_dist_per_frame = 0.3 * self._w  # assume fish can't move more than 30% of tank in one frame time
            max_est_dist = (self._missing_count + 1) * max_dist_per_frame
            if dist > max_est_dist:
                # not considered a valid point
                logging.info("Point rejected due to distance: {pos: %s, dist: %f, max_est_dist: %f}" % (str(self._pos), dist, max_est_dist))
                return -1

            # scale (dist==0)->1.0, (dist==inf)->0.0
            score = 1.0 / (dist+1)

            # Likewise, the new velocity should not be outside of what seems
            # possible w.r.t. acceleration.
            new_vel = pt - self._pos
            accel = numpy.linalg.norm(new_vel - self._vel)
            max_accel_per_frame = 50
            max_accel = (self._missing_count + 1) * max_accel_per_frame
            if accel > max_accel:
                # not considered a valid point
                logging.info("Point rejected due to acceleration: {pos: %s, vel: %s, new_vel: %s, accel: %f}" % (str(self._pos), str(self._vel), str(new_vel), accel))
                return -1

            # consider the acceleration in the score as well
            score *= 1.0 / (accel+1)

            return score
        else:
            # as good as any other, if we have no idea where the fish is to start
            return 0

    def _update_estimates(self, prevpos):
        '''Update estimated velocity based on status and previous data.
        Never estimates position; always just uses last known position.'''
        # self.status is derived from the [just updated] self._missing_count
        if self.status == 'lost':
            # We have no idea where it should be, so no more moving the point.
            self._vel = numpy.zeros(2)
        elif self.status == 'missing':
            # taper velocity to zero
            self._vel *= 0.5
        elif self.status == 'acquired':
            # update estimate velocity if appropriate
            if prevpos is not None:
                # estimated velocity is a [very quickly] decaying average
                alpha = 0.75
                self._vel = alpha * (self._pos - prevpos) + (1-alpha) * self._vel


class Stream(object):
    def __init__(self, source, conf=None, params=None):
        if params is None:
            params = {}

        if type(source) == int:
            # webcam
            assert(conf is not None)
            self._video = self._cam_setup(
                    source,
                    conf['frame_w'],
                    conf['frame_h'],
                    conf['fps'],
                    conf['exposure'])
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

        framecount = self._video.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = self._video.get(cv2.CAP_PROP_FPS)

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

        atexit.register(cap.release)

        # Try setting width/height this way, too, in case we don't have modified OpenCV but this still works.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        # Read a frame, just in case it's needed before setting params
        rval, _ = cap.read()
        if not rval:
            cap.release()
            return None

        # Hacks using v4l2-ctl to set capture parameters we can't control through OpenCV
        v4l2args = []

        # Change AWB setting once to make sure new settings are actually used
        # Not sure why this is required, but it appears to work.
        # Without this, white balance is still somehow automatic even
        # after setting it to manual below.
        self._v4l2_call("--set-ctrl=white_balance_auto_preset=1")

        # Set FPS (OpenCV requests 30, hardcoded)
        v4l2args.append("-p %d" % fps)

        # Set exposure (shutter speed/ISO)
        # exposure_time_absolute is given in multiples of 0.1ms.
        # Make sure fps above is not set too high (exposure time
        # will be adjusted automatically to allow higher frame rate)
        v4l2args.append("--set-ctrl=auto_exposure=1")  # 0=auto, 1=manual
        v4l2args.append("--set-ctrl=exposure_time_absolute=%d" % exposure)

        v4l2args.append("--set-ctrl=white_balance_auto_preset=0")
        v4l2args.append("--set-ctrl=red_balance=1000")
        v4l2args.append("--set-ctrl=blue_balance=1000")

        self._v4l2_call(" ".join(v4l2args))

        logging.info("Set exposure via v4l2-ctl.  Capturing/dumping frames so settings take effect before tracking starts.")
        for _ in range(5):
            cap.read()

        return cap

    @property
    def width(self):
        return int(self._video.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self._video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_frame(self):
        rval, frame = self._video.read()
        if not rval:
            return rval, frame
        return rval, frame
