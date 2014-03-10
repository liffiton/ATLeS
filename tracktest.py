import cv2
import sys


class Process(object):
    def __init__(self):
        # background subtractor
        #self.bgs = cv2.BackgroundSubtractorMOG()
        #self.bgs = cv2.BackgroundSubtractorMOG2()  # not great defaults, and need bShadowDetection to be False
        #self.bgs = cv2.BackgroundSubtractorMOG(history=10, nmixtures=3, backgroundRatio=0.2, noiseSigma=20)
        self.bgs = cv2.BackgroundSubtractorMOG2(history=10, varThreshold=100, bShadowDetection=False)

        # ??? History is ignored?  If learning_rate is > 0, or...?  Unclear.

        # learning rate for background subtractor
        # 0 = never adapts after initial background creation
        # a bit above 0 looks good
        self.learning_rate = 0.001

        # threshold for feature detection
        self.hessian_threshold = 1000

    def sub_bg(self, frame):
        mask = self.bgs.apply(frame, learningRate=self.learning_rate)
        maskrgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        return frame & maskrgb

    def mark_features(self, frame):
        # grayscale for SURF
        gframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        surf = cv2.SURF(self.hessian_threshold)
        keypoints = surf.detect(gframe)

        for kp in keypoints:
            x, y = kp.pt
            cv2.circle(frame, (int(x), int(y)), 2, (0,255,0), -1)
            cv2.circle(frame, (int(x), int(y)), int(kp.response/100), (255,0,0), 1)


def main():
    cv2.namedWindow("preview")

    # Webcam
    #vc = cv2.VideoCapture(0)

    # Test movie
    vc = cv2.VideoCapture("test.avi")

    proc = Process()

    if not vc.isOpened():
        print "Could not open stream..."
        sys.exit(1)

    while True:
        rval, frame = vc.read()

        frame = proc.sub_bg(frame)
        proc.mark_features(frame)

        cv2.imshow("preview", frame)
        key = cv2.waitKey(10)
        if key % 256 == 27:  # exit on ESC
            break

    cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
