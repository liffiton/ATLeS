#
# Source: http://stackoverflow.com/a/11449901
#

import cv2

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

if vc.isOpened():  # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

while rval:
    cv2.imshow("preview", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(10)
    if key % 256 == 27:  # exit on ESC
        break

cv2.destroyWindow("preview")
