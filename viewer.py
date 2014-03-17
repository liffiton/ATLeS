import cv2
import numpy
import sys

import tracking


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
        source = sys.argv[1]
    else:
        # Webcam input
        source = 0

    stream = tracking.Stream(source)

    stream.set_crop([0,140, 0,360])

    # get one frame for testing and setting up dimensions
    rval, frame = stream.get_frame()
    if not rval:
        sys.stderr.write("Error reading from video stream...\n")
        sys.exit(1)

    # create overlay for marking elements on the frame
    # 4 channels for rgb+alpha
    h, w = frame.shape[:2]
    overlay = numpy.zeros((h, w, 4), frame.dtype)

    tracker = tracking.Tracker(stream)

    i = 0
    while True:
        i += 1

        rval = tracker.next_frame(do_track=(i >= 500))
        if not rval:
            # no more frames
            break

        # let the background subtractor learn a good background before doing anything else
        if i < 500:
            continue

        position = tracker.position
        print position
        frame = tracker.frame

        position = tuple(int(x) for x in position)
        cv2.circle(overlay, position, 0, (0,255,0,255))

        # fade previous overlay
        overlay *= 0.99

        ## draw contours
        #for c_i in range(len(proc.contours)):
        #    cv2.drawContours(overlay, proc.contours, c_i, (0,255,0,255), 1)

        # draw centroids
        #for pt in proc.centroids:
        #    cv2.circle(overlay, (int(pt[0]), int(pt[1])), 1, (0,255,0,255))

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
