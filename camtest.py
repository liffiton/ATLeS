#
# camtest.py - Testing the camera, setting parameters, etc.
#

import argparse
import cv2
import subprocess
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
    iso = 0
    exposure = 200
    wb = 0
    rval = (stream is not None)
    while rval:
        rval, frame = stream.get_frame()

        if channel >= 0:
            frame = frame[:,:,channel]

        cv2.imshow("preview", frame)

        key = cv2.waitKey(1)
        if key % 256 == 27:  # exit on ESC
            break
        elif key % 256 == ord(' '):
            cv2.imwrite("camtestout.png", frame)
            print "Saved image to camtestout.png"
        elif key % 256 == ord('c'):
            channel = [1,2,-1,0][channel]
            print "New channel: %d" % channel
        elif key % 256 == ord('i'):
            iso = [1,2,3,4,0][iso]
            subprocess.call(["v4l2-ctl", "--set-ctrl", "iso_sensitivity=%d" % iso])
            print "New ISO: %d" % iso
        elif key % 256 == ord('e'):
            exposure *= 2
            if exposure > 1000:
                exposure = 10
            subprocess.call(["v4l2-ctl", "--set-ctrl", "exposure_time_absolute=%d" % exposure])
            print "New exposure: %d" % exposure
        elif key % 256 == ord('w'):
            wb += 1
            if wb > 9:
                wb = 0
            subprocess.call(["v4l2-ctl", "--set-ctrl", "white_balance_auto_preset=%d" % wb])
            print "New wb: %d" % wb

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
