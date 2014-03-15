import json
import math
import sys


def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)


def main():
    # https://github.com/scanlime/zenphoton/tree/master/hqz
    scene = {}
    scene['resolution'] = [720, 480]
    scene['viewport'] = [0,0, 720,480]
    scene['rays'] = 100000
    scene['exposure'] = 0.3
    scene['objects'] = []
    scene['materials'] = [ [ [0.2, 'd'], [0.2, 't'], [0.6, 'r'] ] ]

    prevpts = []

    i = 0
    frame = 0

    with sys.stdin as f:
        for line in f:
            if i % 3 != 0:
                i += 1
                continue
            i += 1

            # reset lights each frame
            scene['lights'] = []

            pts = line.split()
            pts = [[float(x) for x in pt.split(',')] for pt in pts]

            for pt in pts:
                # find closest in prev
                if prevpts:
                    closest = min(prevpts, key=lambda x: distance(pt, x))
                    add_edge(scene, pt, closest)

            prevpts = pts

            for pt in pts:
                add_light(scene, pt)

            with open("hqz%05d.json" % frame, 'w') as jsonout:
                jsonout.write(json.dumps(scene))

            frame += 1


def add_edge(scene, p0, p1):
    scene['objects'].append([0, p0[0], p0[1], p1[0]-p0[0], p1[1]-p0[1]])


def add_light(scene, pt):
    scene['lights'].append([1, pt[0], pt[1], 0, 0, [0, 360], 0])

if __name__ == '__main__':
    main()
