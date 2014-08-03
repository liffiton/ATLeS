import numpy as np
import sys

_entry_wait = 1  # min seconds between counted entries to top
_freeze_min_time = 0.1  # min seconds to count lack of motion as a "freeze"
_freeze_max_speed = 0.01  # maximum speed to still consider a "freeze"


def main():
    fname = sys.argv[1]

    time, status, x, y = np.loadtxt(
        fname,
        delimiter=',',
        unpack=True,
        dtype={'names': ('time','status','x','y'), 'formats': ('f','S16','f','f')}
    )

    # calculate derivatives and other derived values
    dx = np.ediff1d(x)
    dy = np.ediff1d(y)
    dt = np.ediff1d(time)
    movement = np.matrix([dx,dy])
    dist = np.linalg.norm(movement, axis=0)
    speed = dist / dt
    theta = np.arctan2(dy, dx)  # reversed params are correct for numpy.arctan2
    dtheta = np.ediff1d(theta)
    angular_velocity = dtheta / dt[1:]

    # produce boolean arrays
    valid = (status != 'lost') & (np.roll(status, 1) != 'lost')  # valid if this index *and* previous are both not 'lost'
    valid_count = np.sum(valid)
    in_top = y < 0.5
    frozen = speed < _freeze_max_speed

    # initialize counters, etc.
    last_entry = None
    first_entry = None
    entry_count = 0

    time_in_top = 0
    time_in_bottom = 0

    distance_in_top = 0
    distance_in_bottom = 0

    cur_freeze_time = 0
    total_freeze_time = 0
    freeze_count = 0

    cur_turn_time = 0

    distance_total = 0
    time_total_valid = 0

    for i in xrange(1, len(time)):
        if not valid[i]:
            # cancel any ongoing 'events'
            if cur_freeze_time:
                freeze_count -= 1
                total_freeze_time -= cur_freeze_time
                cur_freeze_time = 0
            if cur_turn_time:
                # TODO
                pass
            continue

        distance_total += dist[i]
        time_total_valid += dt[i]

        # count entries to top
        if in_top[i] and not in_top[i-1] and (last_entry is None or time[i] - last_entry > _entry_wait):
            if first_entry is None:
                first_entry = time[i]
            last_entry = time[i]
            entry_count += 1

        # sum time and distance in top/bottom
        if in_top[i]:
            time_in_top += dt[i]
            distance_in_top += dist[i]
        else:
            time_in_bottom += dt[i]
            distance_in_bottom += dist[i]

        # count freezes
        # "Freeze" = speed < _freeze_max_speed for at least _freeze_min_time seconds
        if frozen[i]:
            if not frozen[i-1]:
                # start of a freeze
                cur_freeze_time = 0
                freeze_count += 1
            total_freeze_time += dt[i]
            cur_freeze_time += dt[i]
        elif frozen[i-1]:
            # end of a freeze
            if cur_freeze_time < _freeze_min_time:
                # don't count this one
                freeze_count -= 1
                total_freeze_time -= cur_freeze_time

        # count erratic movements
        # "Erratic movement" = a string of at least _erratic_count 'turns' in less than _erratic_time seconds
        # "Turn" = abs(angular_velocity) > _turn_vel for at least _turn_time seconds
        # TODO

    print "#Datapoints: %d" % len(valid)
    print "#Valid: %d" % valid_count
    print "%%Valid datapoints: %0.3f" % (valid_count / float(len(valid)))
    print "Total time: %0.2f seconds" % time[-1]
    print "Valid time: %0.2f seconds" % time_total_valid
    print
    print "Total distance traveled: %0.2f [units]" % (distance_total)
    print "Average velocity: %0.3f [units]/second" % (distance_total / time_total_valid)
    print
    print "#Entries to top: %d" % entry_count
    if entry_count:
        print "Time of first entry: %0.2f seconds" % (first_entry)
    print
    print "Time in top:    %0.2f seconds" % time_in_top
    print "Time in bottom: %0.2f seconds" % time_in_bottom
    if time_in_bottom:
        print "Top/bottom time ratio: %0.3f" % (time_in_top/time_in_bottom)
    if entry_count:
        print "Avg. time per entry: %0.2f seconds" % (time_in_top / entry_count)
    print
    print "Distance in top:    %0.3f [units]" % distance_in_top
    print "Distance in bottom: %0.3f [units]" % distance_in_bottom
    if distance_in_bottom:
        print "Top/bottom distance ratio: %0.3f" % (distance_in_top/distance_in_bottom)
    if entry_count:
        print "Avg. distance per entry: %0.3f [units]" % (distance_in_top / entry_count)
    print
    print "#Freezes: %d" % freeze_count
    if freeze_count:
        print "Total time frozen: %0.3f seconds" % total_freeze_time
        print "Avg. time per freeze: %0.3f seconds" % (total_freeze_time / freeze_count)
        print "Freeze frequency: %0.2f per minute" % (60.0*(freeze_count / time_total_valid))

if __name__ == '__main__':
    main()
