import cv2
import math
import random


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
        self._learning_rate = 0.0005

        # element to reuse in erode/dilate
        # RECT is more robust at removing noise in the erode
        #self._element = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
        self._element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))

        # contours and centroids for the most recent frame
        self._contours = None
        self._centroids = None

    def proc_frame(self, frame, verbose=False):
        # reset contours and centroids
        self._contours = None
        self._centroids = None

        # grayscale copy
        self._gframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # subtract background, clean up image
        self._sub_bg()

    def _sub_bg(self):
        mask = self._bgs.apply(self._gframe, learningRate=self._learning_rate)
        #maskrgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        self._gframe = self._gframe & mask

        # filter out single pixels
        self._gframe = cv2.erode(self._gframe, self._element)

        # restore and join nearby regions (in case one fish has a skinny middle...)
        self._gframe = cv2.dilate(self._gframe, self._element)
        self._gframe = cv2.dilate(self._gframe, self._element)
        self._gframe = cv2.dilate(self._gframe, self._element)

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


class ParticleFilter(object):
    def __init__(self, n, dims=[(0,1),(0,1),(-1,1),(-1,1)]):
        self._n = n
        self._repopulate(dims)

    def _repopulate(self, dims):
        print "repop"
        self._particles = []
        for i in range(self._n):
            new_particle = {}
            for i,dim in enumerate(dims):
                new_particle[i] = random.uniform(*dim)
            new_particle['weight'] = 1.0/self._n
            self._particles.append(new_particle)

    @staticmethod
    def distance(p0, p1):
        return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

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
