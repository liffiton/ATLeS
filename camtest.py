#
# Based on: http://stackoverflow.com/a/11449901
#

import cv2
import time

cv2.namedWindow("preview")
cap = cv2.VideoCapture(0)

if cap.isOpened():  # try to get the first frame
    default_res = (cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    print("Frame resolution (default): %s" % str(default_res))
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
    new_res = (cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    print("Frame resolution (new): %s" % str(new_res))

    rval, frame = cap.read()

else:
    rval = False

prevtime = None
while rval:
    curtime = time.time()
    if prevtime is not None:
        print("%dms: %dfps" % (1000*(curtime-prevtime), 1/(curtime-prevtime)))
    prevtime = curtime

    rval, frame = cap.read()

    cv2.imshow("preview", frame)

    key = cv2.waitKey(1)
    if key % 256 == 27:  # exit on ESC
        break

cap.release()
cv2.destroyAllWindows()
