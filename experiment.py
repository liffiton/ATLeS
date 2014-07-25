import argparse
import os
import signal
import sys
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
# Conrol response: static response at position (100,100)
control.set_response(100)

# Stimulus: Visual stimulus or Dummy stimulus (just prints to terminal)
stim = stimulus.VisualStimulus()
#stim = stimulus.DummyStimulus()

# Log directory
logdir = "./logs"

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
        else:
            stim.show(None)

        # tracking performance / FPS
        frames += 1
        if frames % 10 == 0:
            curtime = time.time()
            frame_time = (curtime - prevtime) / 10
            print("%dms: %dfps" % (1000*frame_time, 1/frame_time))
            prevtime = curtime

    cleanup_and_exit()


def get_args():
    parser = argparse.ArgumentParser(description='Zebrafish Skinner box experiment.')
    parser.add_argument('id', type=str, nargs='?', default='',
                        help='experiment ID (optional), added to data output filename')
    parser.add_argument('-t', '--time', type=int, default=None,
                        help='limit the experiment to TIME minutes (default: run forever / until stopped with CTL-C)')
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

    return parser.parse_args()


def cleanup_and_exit():
    stim.end()
    cv2.destroyAllWindows()
    sys.exit(0)


def alarm_handler(signum, frame):
    print("Terminating experiment after timeout.")
    cleanup_and_exit()


def main():
    args = get_args()

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

    # ensure log directory exists
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    # setup log file
    filetimestamp = time.strftime("%Y%m%d-%H%M")
    if args.id:
        datafilename = "%s/%s-%s.csv" % (logdir, filetimestamp, args.id)
    else:
        datafilename = "%s/%s.csv" % (logdir, filetimestamp)

    # setup timeout alarm if needed
    # NOTE: not cross-platform (SIGALRM not available on Windows)
    if args.time:
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(args.time*60)

    with open(datafilename, 'w') as outfile:
        run_experiment(args.watch, stream, outfile)

    cleanup_and_exit()


if __name__ == '__main__':
    main()
