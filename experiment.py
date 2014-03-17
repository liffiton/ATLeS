import tracking
import stimulus


def main():
    stream = tracking.Stream("test.avi")
    track = tracking.Tracker(stream)
    stim = stimulus.DummyStimulus()

    while True:
        rval = track.next_frame()
        if not rval:
            break

        pos = track.position
        if pos[0] > 100:
            stim.show("OOH! %d" % pos[0])


if __name__ == '__main__':
    main()
