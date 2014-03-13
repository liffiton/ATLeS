import cv2
import numpy
import os
import sys
import time


class Process(object):
    def __init__(self):
        # background subtractor
        #self._bgs = cv2.BackgroundSubtractorMOG()
        #self._bgs = cv2.BackgroundSubtractorMOG2()  # not great defaults, and need bShadowDetection to be False
        #self._bgs = cv2.BackgroundSubtractorMOG(history=10, nmixtures=3, backgroundRatio=0.2, noiseSigma=20)
        self._bgs = cv2.BackgroundSubtractorMOG2(history=0, varThreshold=20, bShadowDetection=False)

        # ??? history is ignored?  If learning_rate is > 0, or...?  Unclear.

        # learning rate for background subtractor
        # 0 = never adapts after initial background creation
        # a bit above 0 looks good
        self._learning_rate = 0.001

        # threshold for feature detection
        self._hessian_threshold = 2000

        # element to reuse in erode/dilate
        #self._element = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
        self._element = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))

        # contours for the most recent frame
        self._contours = None

        # overlay for marking elements on a frame
        self._overlay = None

        # processing statistics
        self._nframes = 0
        self._totaltime = 0
        self._avgtime = 0

    def proc_frame(self, frame, sub_bg=False, mark_features=False, mark_contours=False, mark_centroids=False, verbose=False):
        # time processing
        start_time = time.time()

        # reset contours
        self._contours = None

        # create overlay for marking elements on the frame
        if self._overlay is None:
            # 4 channels for rgb+alpha
            self._overlay = numpy.zeros((frame.shape[0], frame.shape[1], 4), frame.dtype)
        self._overlay = numpy.zeros((frame.shape[0], frame.shape[1], 4), frame.dtype)

        # copy the frame for performing analysis and marking results
        self._proc_frame = frame.copy()

        if sub_bg:
            self._sub_bg()

        # grayscale copy for SURF and contours
        self._gframe = cv2.cvtColor(self._proc_frame, cv2.COLOR_BGR2GRAY)

        if mark_features:
            self._mark_features()

        if mark_contours:
            self._mark_contours()

        if mark_centroids:
            self._mark_centroids()

        # statistics
        frame_time = time.time() - start_time
        self._totaltime += frame_time
        self._nframes += 1
        if verbose:
            print("Frame time: %.3f sec\nAvg. time:  %.3f sec (max %dfps)\n" % (frame_time, self._totaltime/self._nframes, int(self._nframes/self._totaltime)))

        #self._overlay *= 0.99
        return self._overlay

    def _sub_bg(self):
        mask = self._bgs.apply(self._proc_frame, learningRate=self._learning_rate)
        maskrgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        self._proc_frame = self._proc_frame & maskrgb

    def _mark_features(self):
        surf = cv2.SURF(self._hessian_threshold)
        keypoints = surf.detect(self._gframe)

        for kp in keypoints:
            x, y = kp.pt
            # dot at keypoint location
            cv2.circle(self._overlay, (int(x), int(y)), 2, (0,255,0,255), -1)
            # circle with size = keypoint response weight
            #cv2.circle(self._overlay, (int(x), int(y)), int(kp.response/100), (255,0,0,255), 1)

    def _get_contours(self):
        # filter out single pixels
        self._gframe = cv2.erode(self._gframe, self._element)
        # restore and join nearby regions (in case one fish has a skinny middle...)
        self._gframe = cv2.dilate(self._gframe, self._element)
        self._gframe = cv2.dilate(self._gframe, self._element)
        self._gframe = cv2.dilate(self._gframe, self._element)

        # find contours
        self._contours, _ = cv2.findContours(self._gframe, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def _mark_contours(self):
        if not self._contours:
            self._get_contours()

        for i in range(len(self._contours)):
            cv2.drawContours(self._overlay, self._contours, i, (0,255,0,255), 1)

    def _mark_centroids(self):
        if not self._contours:
            self._get_contours()

        for contour in self._contours:
            moments = cv2.moments(contour)
            centroid_x = moments['m10'] / moments['m00']
            centroid_y = moments['m01'] / moments['m00']
            # dot at centroid
            cv2.circle(self._overlay, (int(centroid_x), int(centroid_y)), 2, (0,255,0,255), -1)


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

    i = 0
    while True:
        i += 1

        # capture one frame
        rval, frame = video.read()
        if not rval:
            break

        # process the frame
        overlay = proc.proc_frame(frame, sub_bg=True, mark_features=False, mark_contours=True, mark_centroids=False, verbose=True)

        # display the frame and handle the event loop
        draw = alphablend(frame, overlay)
        cv2.imshow("preview", draw)

        key = cv2.waitKey(1)
        if key % 256 == 27:  # exit on ESC
            break

    cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
