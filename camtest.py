#
# Based on: http://stackoverflow.com/a/11449901
#

import cv2
import os
import time

width = 320
height = 240
fps = 8

cv2.namedWindow("preview")
cap = cv2.VideoCapture(0)

if cap.isOpened():  # try to get the first frame
    default_res = (cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    print("Frame resolution (default): %s" % str(default_res))
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, height)
    new_res = (cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    print("Frame resolution (new): %s" % str(new_res))

    rval, frame = cap.read()

else:
    rval = False

# Drop framerate to 8fps (OpenCV requests 30fps by default, which rpi can't handle)
os.system("v4l2-ctl -p %d" % fps)

prevtime = None
while rval:
    curtime = time.time()
    if prevtime is not None:
        print("%dms: %dfps" % (1000*(curtime-prevtime), 1/(curtime-prevtime)))
    prevtime = curtime

    _,frame = cap.read()

    cv2.imshow("preview", frame)

    key = cv2.waitKey(1)
    if key % 256 == 27:  # exit on ESC
        break

cap.release()
cv2.destroyAllWindows()
