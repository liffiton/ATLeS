import tracking
import controllers
import stimulus

# An example experiment with:
#  Tracking: Simple
#  Controller: Fixed 5 second interval
#  Behavior: xpos > 100
#  Stimulus: Printout to terminal (dummy stimulus)


def main():
    stream = tracking.Stream("test.avi")
    track = tracking.Tracker(stream)
    control = controllers.FixedIntervalController(response_interval=5)
    stim = stimulus.DummyStimulus()

    while True:
        rval = track.next_frame()
        if not rval:
            break

        pos = track.position
        if pos[0] > 100:
            control.add_hit('x>100')
            if control.do_response():
                stim.show("OOH! %d" % pos[0])


if __name__ == '__main__':
    main()
