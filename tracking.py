import cv2
import numpy
import os
import sys


class Process(object):
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


def alphablend(img, overlay):
    ret = img.copy()
    for c in 0,1,2:
        alpha = overlay[:,:,3]
        ret[:,:,c] = ret[:,:,c]*(1-alpha/255.0) + overlay[:,:,c]*(alpha/255.0)
    return ret


def main():
    cv2.namedWindow("preview")

    if len(sys.argv) > 1:
        # Video file input
        filename = sys.argv[1]
        if os.path.exists(filename):
            video = cv2.VideoCapture(filename)
        else:
            print("Input file not found: %s" % filename)
            sys.exit(1)
    else:
        # Webcam input
        video = cv2.VideoCapture(0)

    proc = Process()

    if not video.isOpened():
        print "Could not open video stream..."
        sys.exit(1)

    # get one frame for testing and setting up overlay
    rval, frame = video.read()
    if rval:
        # create overlay for marking elements on the frame
        # 4 channels for rgb+alpha
        overlay = numpy.zeros((frame.shape[0], frame.shape[1], 4), frame.dtype)
    else:
        print "Error reading from video stream..."
        sys.exit(1)

    i = 0
    while True:
        i += 1

        # capture one frame
        rval, frame = video.read()
        if not rval:
            break

        # process the frame
        proc.proc_frame(frame, verbose=True)

        # fade previous overlay
        overlay *= 0.99

        ## draw contours
        #for i in range(len(proc.contours)):
        #    cv2.drawContours(overlay, proc.contours, i, (0,255,0,255), 1)

        # draw centroids
        for pt in proc.centroids:
            cv2.circle(overlay, (int(pt[0]), int(pt[1])), 1, (0,255,0,255))

        # display the frame and handle the event loop
        draw = alphablend(frame, overlay)
        cv2.imshow("preview", draw)

        key = cv2.waitKey(1)
        if key % 256 == 27:  # exit on ESC
            break

    cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
