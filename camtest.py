#
# Based on: http://stackoverflow.com/a/11449901
#

import cv2
import time

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

if vc.isOpened():  # try to get the first frame
    default_res = (cv2.cv.CV_CAP_PROP_FRAME_WIDTH, cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    #print("Frame resolution (default): %s" % str(default_res))
    vc.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
    vc.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
    new_res = (cv2.cv.CV_CAP_PROP_FRAME_WIDTH, cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
    #print("Frame resolution (new): %s" % str(new_res))

    rval, frame = vc.read()

else:
    rval = False

prevtime = None
while rval:
    curtime = time.time()
    if prevtime is not None:
        print("%dms: %dfps" % (1000*(curtime-prevtime), 1/(curtime-prevtime)))
    prevtime = curtime

    cv2.imshow("preview", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(1)
    if key % 256 == 27:  # exit on ESC
        break

cv2.destroyWindow("preview")
