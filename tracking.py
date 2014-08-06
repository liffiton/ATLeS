import cv2
import logging
import math
import os
import random
import sys


def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)


class FrameProcessor(object):
    def __init__(self):
        # background subtractor
        #self._bgs = cv2.BackgroundSubtractorMOG()
        #self._bgs = cv2.BackgroundSubtractorMOG2()  # not great defaults, and need bShadowDetection to be False
        #self._bgs = cv2.BackgroundSubtractorMOG(history=10, nmixtures=3, backgroundRatio=0.2, noiseSigma=20)
        self._bgs = cv2.BackgroundSubtractorMOG2(history=0, varThreshold=10, bShadowDetection=False)

        # ??? history is ignored?  Only if learning_rate is > 0, or...?  Unclear.

        # Learning rate for background subtractor.
        # 0 = never adapts after initial background creation.
        # A bit above 0 looks good.
        # Lower values are better for detecting slower movement, though it
        # takes a bit of time to learn the background initially.
        #self._learning_rate = 0.0005  # for ~30fps video
        self._learning_rate = 0.005  # for 3fps video?

        # element to reuse in erode/dilate
        # RECT is more robust at removing noise in the erode
        #self._element = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
        self._element33 = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        self._element55 = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))

        # contours and centroids for the most recent frame
        self._contours = None
        self._centroids = None

    def process_frame(self, frame):
        # reset contours and centroids
        self._contours = None
        self._centroids = None

        # grayscale copy
        #self._gframe = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160,120))
        self._gframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # subtract background, clean up image
        self._sub_bg()

    def _sub_bg(self):
        mask = self._bgs.apply(self._gframe, learningRate=self._learning_rate)
        self._gframe = self._gframe & mask

        # filter out single pixels
        self._gframe = cv2.erode(self._gframe, self._element33)

        # restore and join nearby regions (in case one fish has a skinny middle...)
        self._gframe = cv2.dilate(self._gframe, self._element55)

    def _get_contours(self):
        # find contours
        self._contours, _ = cv2.findContours(self._gframe, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def _get_centroids(self):
        if not self._contours:
            self._get_contours()

        self._centroids = []

        for contour in self._contours:
            moments = cv2.moments(contour)
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
    def __init__(self, w, h, conf):
        self._w = float(w)  # frame width (for scaling coordinates)
        self._h = float(h)  # frame height
        self._tank_min_x = float(conf['tank_min_x'])   # left edge of tank, in normalized x-coordinates
        self._tank_max_x = float(conf['tank_max_x'])   # right edge of tank, in normalized x-coordinates
        self._tank_min_y = float(conf['tank_min_y'])   # bottom edge of tank, in normalized y-coordinates
        self._tank_max_y = float(conf['tank_max_y'])   # top edge of tank, in normalized y-coordinates
        self._fov_w = float(conf['fov_width'])   # field of view width at fish tank (in meters)
        self._fov_h = float(conf['fov_height'])  # field of view height at fish tank (in meters)
        self._pos = [0,0]
        self._vel = [0,0]
        self._missing_count = 100   # How many frames have we not had something to track?
                                    # Initialized to 100 so status() is initially 'lost'

    @property
    def _speed(self):
        return math.sqrt(self._vel[0]**2 + self._vel[1]**2)

    @property
    def position_pixel(self):
        '''Return the position in pixel coordinates.'''
        return tuple(self._pos)

    @property
    def position_frame(self):
        '''Return the position in frame coordinates.
        Both x- and y-coordinates are scaled to 0.0-1.0 relative to the entire captured image.
        NOTE: y-axis is inverted from pixel coordinates, so y=0.0 is the **bottom** of the frame.
        '''
        return (self._pos[0] / self._w, 1.0 - self._pos[1] / self._h)

    @property
    def position_tank(self):
        '''Return the position in tank coordinates.
        Both x- and y-coordinates are scaled to 0.0-1.0 relative to the view of the tank.
        NOTE: y-axis is inverted from pixel coordinates, so y=0.0 is the **bottom** of the tank.
        '''
        return (
            (self._pos[0] / self._w - self._tank_min_x) / (self._tank_max_x - self._tank_min_x),
            1.0 - (self._pos[1] / self._h - self._tank_min_y) / (self._tank_max_y - self._tank_min_y)
        )

    @property
    def status(self):
        # is anything currently being tracked
        if self._missing_count == 0:
            return 'acquired'
        elif 0 < self._missing_count < 5:
            return 'missing'
        else:
            return 'lost'

    def update(self, obs):
        if obs:
            closest = min(obs, key=lambda pt: distance(pt, self._pos))
        else:
            closest = None

        if self.status == 'lost':
            self._vel = [0,0]
            if closest is None:
                self._missing_count += 1
                # just use the last known position
                return
            else:
                # closest position is new acquired position
                self._missing_count = 0
                self._pos = list(closest)

        else:
            # satus is missing or acquired

            # skip if no centroids or if closest is more than 50px away (XXX: magic number!) but velocity is not 0.0 (i.e. no estimate yet)
            if closest is None or distance(closest, self._pos) > 50 and self._speed != 0.0:
                self._missing_count += 1

                # use the stored velocity
                self._pos[0] += self._vel[0]
                self._pos[1] += self._vel[1]
            else:
                self._missing_count = 0
                dx = closest[0] - self._pos[0]
                dy = closest[1] - self._pos[1]

                # update estimate position
                self._pos = list(closest)

                # update estimate velocity as a decaying average
                alpha = 0.4
                self._vel[0] = alpha * dx + (1-alpha) * self._vel[0]
                self._vel[1] = alpha * dy + (1-alpha) * self._vel[1]


class ParticleFilter(object):
    """A hacked-together, somewhat bogus particle filter... use at your own risk."""
    def __init__(self, n, dims=[(0,1),(0,1),(-1,1),(-1,1)]):
        self._n = n
        self._repopulate(dims)

    def _repopulate(self, dims):
        self._particles = []
        for i in range(self._n):
            new_particle = {}
            for i,dim in enumerate(dims):
                new_particle[i] = random.uniform(*dim)
            new_particle['weight'] = 1.0/self._n
            self._particles.append(new_particle)

    def update(self):
        for particle in self._particles:
            particle[0] += random.gauss(particle[2], particle[2]*0.1)
            #particle[0] += particle[2]
            particle[1] += random.gauss(particle[3], particle[3]*0.1)
            #particle[1] += particle[3]

    def measurement(self, position):
        weightsum = 0.0
        # reweight particles based on position measurement
        for p in self._particles:
            p['weight'] = math.exp(-self.distance(position, (p[0],p[1]))**2 / 10000)
            weightsum += p['weight']
            p[2] = position[0] - p[0]
            p[3] = position[1] - p[1]

        if weightsum == 0.0:
            self._repopulate([(position[0],position[0]), (position[1],position[1]), (-1,1), (-1,1)])
        else:
            # normalize weights
            while weightsum < 1.0:
                for p in self._particles:
                    p['weight'] /= weightsum
                weightsum = sum(p['weight'] for p in self._particles)

        # resample
        new_particles = []
        for i in range(self._n):
            rnd = random.random()
            i = 0
            while rnd >= 0.0 and i < self._n:
                chosen = self._particles[i]
                rnd -= chosen['weight']
                i += 1
            new_particles.append(chosen.copy())

        self._particles = new_particles

    @property
    def estimate(self):
        return max(self._particles, key=lambda x: x['weight'])


class Stream(object):
    def __init__(self, source, w=160, h=120, params=None, fps=6):
        self._crop = None
        if params is None:
            params = {}

        if type(source) == int:
            # webcam
            self._video = cv2.VideoCapture(source, w, h)
            # try to set given parameters
            for key, value in params.items():
                self._video.set(key, value)
                newval = self._video.get(key)
                if newval != value:
                    print "Unable to set %s to %s, got %s." % (key, value, newval)
            # hack to set FPS (OpenCV requests 30, hardcoded)
            os.system("v4l2-ctl -p %d" % fps)
        elif os.path.isfile(source):
            # video file
            self._video = cv2.VideoCapture(source)
        else:
            logging.error("Input file not found: %s\n" % source)
            sys.exit(1)

        if not self._video.isOpened():
            logging.error("Could not open video stream...\n")
            sys.exit(1)

    @property
    def width(self):
        return self._video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)

    @property
    def height(self):
        return self._video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)

    def set_crop(self, newcrop):
        '''Set the cropping for returned frames.

        Inputs:
          newcrop: (x1,x2, y1,y2) tuple or list of integers.
                   Frame will be cropped to x=(x1..x2-1), y=(y1..y2-1).
        '''
        self._crop = newcrop

    def get_frame(self):
        rval, frame = self._video.read()
        if not rval:
            return rval, frame
        if self._crop:
            c = self._crop
            frame = frame[c[0]:c[1], c[2]:c[3]]
        return rval, frame
