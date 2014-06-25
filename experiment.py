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
force_stimulus = False
width = 160
height = 120
fps = 3


def main():
    if test_input:
        stream = tracking.Stream("test.avi")
    else:
        params = {}
        #params[cv2.cv.CV_CAP_PROP_FRAME_WIDTH] = width
        #params[cv2.cv.CV_CAP_PROP_FRAME_HEIGHT] = height
        params[cv2.cv.CV_CAP_PROP_EXPOSURE] = 0.001
        # NOTE: requires my hacked version of OpenCV w/ width/height constructor
        stream = tracking.Stream(0, w=width, h=height, params=params, fps=fps)

    track = tracking.Tracker()
    #control = controllers.FixedIntervalController(response_interval=5)
    control = controllers.FixedRatioController(1)
    #stim = stimulus.VisualStimulus()
    stim = stimulus.DummyStimulus()

    if see_frames:
        cv2.namedWindow("preview")

    prevtime = time.time()
    frames = 0

    while True:
        stim.blank()
        rval, frame = stream.get_frame()
        stim.unblank()

        if not rval:
            break

        track.process_frame(frame)

        pos = track.position
        print pos
        print track.status

        if see_frames:
            position = tuple(int(x) for x in pos)
            cv2.circle(frame, position, 5, (0,255,0,255))
            cv2.imshow("preview", frame)
            if cv2.waitKey(1) % 256 == 27:
                break

        if force_stimulus:
            stim.show(200)
        else:
            if pos[0] > 100:
                control.add_hit('x>100')
                if control.do_response():
                    stim.show(pos[0])

        frames += 1
        if frames % 10 == 0:
            curtime = time.time()
            frame_time = (curtime - prevtime) / 10
            print("%dms: %dfps" % (1000*frame_time, 1/frame_time))
            prevtime = curtime

    stim.end()

    if see_frames:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
