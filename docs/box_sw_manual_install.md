---
title: (Manual) Box Software Setup
---

Most people will not need to use the following instructions.
They are provided for anyone who wants to set up the ATLeS box software environment themselves.
The easiest way to install and use the software is to [install a provided OS image](box_sw_install).

# Installing FishyCam from Scratch

If you are comfortable working in a Linux deveopment environment, you can install the needed software yourself.
Start with a clean install of [Raspbian](https://www.raspberrypi.org/downloads/raspbian/).

## Python Package Dependencies

Before installing the python modules themselves, install the required tools:

    $ sudo apt-get install build-essential pkg-config

... and libraries:

    $ sudo apt-get install python-dev libpng-dev libfreetype6-dev

Many python packages are most easily installed via pip.  If you need to install pip, refer to [these instructions](https://pip.pypa.io/en/stable/installing/).

Each of the fishbox scripts relies on a specific set of python modules.

### fishweb.py

Depends on:
 * bottle
 * cherrypy
 * Jinja2
 * wtforms
 * python-daemon
 * matplotlib
 * numpy
 * rpyc
 * zeroconf

Install by running:

    $ pip install --user -U -r requirements_fishweb.txt

If you need to install matplotlib on an RPi, you may have to work around an issue with pip.  'pip install matplotlib' fails on a stock RPi (both models 1 and 2) with a memory error.  To work around this, install it without using the cache (thanks to: [http://stackoverflow.com/a/31526029](http://stackoverflow.com/a/31526029)):

    $ pip install --user --no-cache-dir matplotlib

 
### fishremote.py

Depends on:
 * plumbum
 * rpyc
 * zeroconf

Install by running:

    $ pip install --user -U -r requirements_fishremote.txt


### fishbox.py

Depends on:
 * cv2         (for OpenCV)
 * smbus       (for reading sensor values)
 * wiringpi    (for controlling light bar via PWM)

To install cv2, see [opencv_notes](opencv_notes.txt).

To install smbus:

    $ sudo apt-get install python-smbus


## Runtime Dependencies

Additional packages required to run the fishbox/fishremote software:

 * rsync

Install with:

    $ sudo apt-get install rsync

Both the camera and i2c need to be enabled using raspi-config.  Run
`sudo raspi-config` and enable both (i2c is under "advanced options").

To use the camera via v4l, the `bcm2835-v4l2` module must be loaded.
For the i2c interface (for sensors), the `i2c-dev` module must be loaded.
To have the modules loaded automatically on boot, add each to `/etc/modules`, one per line:

    bcm2835-v4l2
    i2c-dev

Alternatively, modprobe can be used to load them manually at any time:

    $ sudo modprobe bcm2835-v4l2
    $ sudo modprobe i2c-dev

