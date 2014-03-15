import cv2
import math
import numpy
import os
import sys

import tracking


def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)


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

    proc = tracking.FrameProcessor()

    if not video.isOpened():
        print "Could not open video stream..."
        sys.exit(1)

    # get one frame for testing and setting up dimensions
    rval, frame = video.read()
    if not rval:
        print "Error reading from video stream..."
        sys.exit(1)

    # create overlay for marking elements on the frame
    # 4 channels for rgb+alpha
    h, w = frame.shape[:2]
    #h, w = 120, 360
    overlay = numpy.zeros((h, w, 4), frame.dtype)

    pf = tracking.ParticleFilter(100, [(0, w-1), (0, h-1), (-1, 1), (-1, 1)])

    i = 0
    while True:
        i += 1

        # capture one frame
        rval, frame = video.read()
        if not rval:
            break

        #frame = frame[:120, :360]

        # process the frame
        proc.proc_frame(frame, verbose=True)

        # let the background subtractor learn a good background before doing anything else
        if i < 500:
            continue

        # use the filter
        if proc.centroids:
            closest = min(proc.centroids, key=lambda pt: distance(pt, (pf.estimate[0], pf.estimate[1])))
            pf.update()
            pf.measurement(closest)
            cv2.line(overlay, (int(pf.estimate[0]), int(pf.estimate[1])), (int(closest[0]), int(closest[1])), (0,0,255,255))
            cv2.circle(overlay, (int(pf.estimate[0]), int(pf.estimate[1])), 1, (0,255,0,255))

        # fade previous overlay
        overlay *= 0.99

        ## draw contours
        #for c_i in range(len(proc.contours)):
        #    cv2.drawContours(overlay, proc.contours, c_i, (0,255,0,255), 1)

        # draw centroids
        #for pt in proc.centroids:
        #    cv2.circle(overlay, (int(pt[0]), int(pt[1])), 1, (0,255,0,255))

        # draw filtered points
        #for filt in filters:
            #cv2.circle(overlay, (int(filt.estimate[0]), int(filt.estimate[1])), 1, (0,0,255,255))

        # display the frame and handle the event loop
        if i % 10 == 0:
            draw = alphablend(frame, overlay)
            #draw = overlay
            cv2.imshow("preview", draw)

        key = cv2.waitKey(1)
        if key % 256 == 27:  # exit on ESC
            break

    cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
