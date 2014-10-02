#
# camtest.py - Testing the camera, setting parameters, etc.
#

import argparse
import cv2
import os
import time


def cam_setup(args):
    try:
        cap = cv2.VideoCapture(0, args.width, args.height)
    except TypeError:
        # Don't have our modified version of OpenCV w/ width/height args
        print("WARNING: Unmodified OpenCV installation; no width/height control for capture.")
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return None

    #default_res = (cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    #print("Frame resolution (default): %s" % str(default_res))
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, args.height)
    new_res = (cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    print("Frame resolution: %s" % str(new_res))

    # Read a frame, just in case it's needed before setting params
    rval, _ = cap.read()
    if not rval:
        return None

    # Set frame rate
    os.system("v4l2-ctl -p %d" % args.fps)

    # Turn off white balance (seems to need to be reset to non-zero first, then zero)
    os.system("v4l2-ctl --set-ctrl=white_balance_auto_preset=1")
    os.system("v4l2-ctl --set-ctrl=white_balance_auto_preset=0")

    # Set shutter speed
    # exposure_time_absolute is given in multiples of 0.1ms.
    # Make sure fps above is not set too high (exposure time
    # will be adjusted automatically to allow higher frame rate)
    os.system("v4l2-ctl --set-ctrl=auto_exposure=1")
    os.system("v4l2-ctl --set-ctrl=exposure_time_absolute=%d" % args.exposure)

    return cap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-W', '--width', type=int, nargs='?', default=320)
    parser.add_argument('-H', '--height', type=int, nargs='?', default=240)
    parser.add_argument('-f', '--fps', type=int, nargs='?', default=10)
    parser.add_argument('-e', '--exposure', type=int, nargs='?', default=200)
    args = parser.parse_args()

    cv2.namedWindow("preview")

    cap = cam_setup(args)

    prevtime = time.time()
    frames = 0
    channel = -1
    rval = (cap is not None)
    while rval:
        rval, frame = cap.read()

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

    if cap:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
