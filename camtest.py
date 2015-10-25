#
# camtest.py - Testing the camera, setting parameters, etc.
#

import argparse
import cv2
import time

from fishbox import tracking


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-W', '--width', type=int, nargs='?', default=320)
    parser.add_argument('-H', '--height', type=int, nargs='?', default=240)
    parser.add_argument('-f', '--fps', type=int, nargs='?', default=10)
    parser.add_argument('-e', '--exposure', type=int, nargs='?', default=200)
    args = parser.parse_args()

    conf = {
        'frame_w': args.width,
        'frame_h': args.height,
        'fps': args.fps,
        'exposure': args.exposure
    }
    params = {}
    stream = tracking.Stream(0, conf, params)

    cv2.namedWindow("preview")

    prevtime = time.time()
    frames = 0
    channel = -1
    rval = (stream is not None)
    while rval:
        rval, frame = stream.get_frame()

        if channel >= 0:
            frame = frame[:,:,channel]

        cv2.imshow("preview", frame)

        key = cv2.waitKey(1)
        if key % 256 == 27:  # exit on ESC
            break
        elif key > 0:
            channel = [1,2,-1,0][channel]

        frames += 1
        if frames % 10 == 0:
            curtime = time.time()
            frame_time = (curtime-prevtime) / 10
            if prevtime is not None:
                print("%dms: %dfps" % (1000*frame_time, 1/frame_time))
            prevtime = curtime

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
