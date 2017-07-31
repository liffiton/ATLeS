#!/usr/bin/env python3

import time

from box import sensors


def main():
    _sensors = sensors.Sensors(read_interval=1)
    _sensors.begin()
    while True:
        print(_sensors.get_latest())
        time.sleep(1)


if __name__ == '__main__':
    main()
