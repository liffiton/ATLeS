import cv2
import math
import os
import sys

import tracking


def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)


def main():
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

    proc = tracking.FrameProcessor()

    if not video.isOpened():
        print "Could not open video stream..."
        sys.exit(1)

    # get one frame for testing and setting up dimensions
    rval, frame = video.read()
    if not rval:
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

        # let the background subtractor learn a good background before doing anything else
        if i < 500:
            continue

        # export centroids
        for pt in proc.centroids:
            sys.stdout.write("%f,%f " % (pt[0], pt[1]))
        sys.stdout.write('\n')


if __name__ == '__main__':
    main()
