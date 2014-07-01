import argparse
import time

import cv2

import tracking
import controllers
import stimulus

#############################################################
# Experiment setup (tracking, controller, stimulus, and test)

# Tracking: Simple
track = tracking.Tracker()

# Controller: Fixed interval or fixed ratio
#control = controllers.FixedIntervalController(response_interval=3)
control = controllers.FixedRatioController(1)
# Currently: static response at position (100,100)
control.set_response(100)

# Stimulus: Visual stimulus or Dummy stimulus (just prints to terminal)
stim = stimulus.VisualStimulus()
#stim = stimulus.DummyStimulus()

# Behavior test: xpos > 10
def behavior_test(pos):
    return pos[0] > 10
#
####################################################################


def run_experiment(watch, stream, outfile):
    stim.begin()
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

        # Record data
        outfile.write("%0.4f,%s,%d,%d\n" % (time.time(), track.status, pos[0], pos[1]))

        if watch:
            position = tuple(int(x) for x in pos)
            cv2.circle(frame, position, 5, (0,255,0,255))
            cv2.imshow("preview", frame)
            if cv2.waitKey(1) % 256 == 27:
                break

        if behavior_test(pos):
            control.add_hit(str(pos))
            response = control.get_response()
            stim.show(response)

        # tracking performance / FPS
        frames += 1
        if frames % 10 == 0:
            curtime = time.time()
            frame_time = (curtime - prevtime) / 10
            print("%dms: %dfps" % (1000*frame_time, 1/frame_time))
            prevtime = curtime

    stim.end()


def main():
    parser = argparse.ArgumentParser(description='Zebrafish Skinner box experiment.')
    parser.add_argument('id', type=str, default='',
                        help='experiment ID (optional), added to data output filename')
    # TODO: separate frequent/useful arguments from infrequest/testing arguments (below
    parser.add_argument('-w', '--watch', action='store_true',
                        help='create a window to see the camera view and tracking information')
    parser.add_argument('-W', '--width', type=int, default=160,
                        help='video capture resolution width (default: 160)')
    parser.add_argument('-H', '--height', type=int, default=120,
                        help='video capture resolution height (default: 120)')
    parser.add_argument('--fps', type=int, default=5,
                        help='video capture frames per second (default: 5) -- also affects rate of stimulus blinking and behavior/position tests.')
    parser.add_argument('--vidfile', type=str,
                        help='read video input from the given file (for testing purposes)')

    args = parser.parse_args()


    if args.vidfile:
        stream = tracking.Stream(args.vidfile)
    else:
        params = {}
        #params[cv2.cv.CV_CAP_PROP_FRAME_WIDTH] = args.width
        #params[cv2.cv.CV_CAP_PROP_FRAME_HEIGHT] = args.height
        #params[cv2.cv.CV_CAP_PROP_EXPOSURE] = 0.001
        # NOTE: requires my hacked version of OpenCV w/ width/height constructor
        stream = tracking.Stream(0, w=args.width, h=args.height, params=params, fps=args.fps)

    if args.watch:
        cv2.namedWindow("preview")

    filetimestamp = time.strftime("%Y%m%d-%H%M")
    if args.id:
        datafilename = "%s-%s.csv" % (filetimestamp, args.id)
    else:
        datafilename = "%s.csv" % filetimstamp
    with open(datafilename, 'w') as outfile:
        run_experiment(args.watch, stream, outfile)

    if args.watch:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
