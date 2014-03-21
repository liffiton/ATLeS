import cv2
import time

import tracking
import controllers
import stimulus

# An example experiment with:
#  Tracking: Simple
#  Controller: Fixed 5 second interval
#  Behavior: xpos > 100
#  Stimulus: Visual stimulus

# Testing setup (hacked in here for now... TODO: cleanup.)
test_input = False
see_frames = True
force_stimulus = True


def main():
    if test_input:
        stream = tracking.Stream("test.avi")
    else:
        params = {}
        params[cv2.cv.CV_CAP_PROP_FRAME_WIDTH] = 320
        params[cv2.cv.CV_CAP_PROP_FRAME_HEIGHT] = 240
        params[cv2.cv.CV_CAP_PROP_EXPOSURE] = 0.001
        stream = tracking.Stream(0, params)

    track = tracking.Tracker(stream)
    control = controllers.FixedIntervalController(response_interval=5)
    stim = stimulus.VisualStimulus()

    if see_frames:
        cv2.namedWindow("preview")

    while True:
        print time.time()
        stim.blank(delay=0.25)
        rval = track.next_frame()
        stim.unblank()
        if not rval:
            break

        if see_frames:
            cv2.imshow("preview", track.frame)
            if cv2.waitKey(1) % 256 == 27:
                break

        pos = track.position
        if force_stimulus:
            stim.show(200)
        else:
            if pos[0] > 100:
                control.add_hit('x>100')
                if control.do_response():
                    stim.show(pos[0])

    stim.end()

    if see_frames:
        cv2.destroyWindow("preview")


if __name__ == '__main__':
    main()
