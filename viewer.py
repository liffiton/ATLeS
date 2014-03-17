import cv2
import numpy
import sys
import time

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
    prev_time = None
    while True:
        # handle the event loop no matter what
        key = cv2.waitKey(1)
        if key % 256 == 27:  # exit on ESC
            break

        if prev_time is not None:
            print time.time() - prev_time
        prev_time = time.time()

        i += 1
        initializing = (i < 200)

        rval = tracker.next_frame(do_track=(not initializing))
        if not rval:
            # no more frames
            break

        frame = tracker.frame

        # let the background subtractor learn a good background before doing anything else
        if initializing:
            cv2.imshow("preview", frame)
            continue

        position = tracker.position
        status = tracker.status
        print "%10s %s" % (status, str(position))

        position = tuple(int(x) for x in position)
        if status == 'acquired':
            cv2.circle(overlay, position, 0, (0,255,0,255))
        elif status == 'missing':
            cv2.circle(overlay, position, 2, (255,0,0,255))
        elif status == 'lost':
            cv2.circle(overlay, position, 5, (0,0,255,255))

        # fade previous overlay
        overlay *= 0.999

        ## draw contours
        #for c_i in range(len(proc.contours)):
        #    cv2.drawContours(overlay, proc.contours, c_i, (0,255,0,255), 1)

        # draw centroids
        #for pt in proc.centroids:
        #    cv2.circle(overlay, (int(pt[0]), int(pt[1])), 1, (0,255,0,255))

        # display the frame
        if i % 1 == 0:
            draw = alphablend(frame, overlay)
            #draw = overlay
            cv2.imshow("preview", draw)

    cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
