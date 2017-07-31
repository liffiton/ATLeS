---
title: (Manual) Box Software Setup
---

Most people will not need to use the following instructions.
They are provided for anyone who wants to set up the ATLeS box software environment themselves.
The easiest way to install and use the software is to [install a provided OS image](box_sw_install).
The following installation steps require that you are comfortable working in a Linux development environment.

# Installing ATLeS Software

The software can be run on any unix-like system.  A common setup will install `atles_web.py` on a server
(it has been tested under Linux and Cygwin thus far), while `atles_remote.py` will run on one or more Raspberry Pi
nodes in the experiment boxes.
When installing on a Raspberry Pi, start with a clean install of [Raspbian](https://www.raspberrypi.org/downloads/raspbian/).

## Python Package Dependencies

Before installing the python modules themselves, install the required tools:

    $ sudo apt-get install build-essential pkg-config

... and libraries:

    $ sudo apt-get install python-dev libpng-dev libfreetype6-dev

Many python packages are most easily installed via pip.  If you need to install pip, refer to [these instructions](https://pip.pypa.io/en/stable/installing/).

Each of the ATLeS scripts relies on a specific set of python modules.

### atles\_web.py

Depends on:
 * bottle
 * bottle-sqlalchemy
 * Jinja2
 * wtforms
 * python-daemon
 * matplotlib
 * numpy
 * pandas
 * rpyc
 * sqlalchemy
 * waitress
 * zeroconf

Install by running:

    $ pip3 install --user -U -r requirements_web.txt

If you want to install matplotlib on an RPi, you may have to work around an issue with pip.  A standard pip install of matplotlib fails on a stock RPi (both models 1 and 2) with a memory error.  To work around this, install it without using the cache (thanks to: [http://stackoverflow.com/a/31526029](http://stackoverflow.com/a/31526029)):

    $ pip3 install --user --no-cache-dir matplotlib

 
### atles\_remote.py and atles\_box.py

Depend on:
 * Installable from PyPI via pip:
   * numpy
   * plumbum
   * rpyc
   * zeroconf
   * wiringpi    (for controlling lights via PWM)
 * Separate installs:
   * cv2         (OpenCV)
   * smbus       (for reading sensor values)

Install PyPI packages by running:

    $ pip3 install --user -U -r requirements_remote.txt

To install smbus:

    $ sudo apt-get install python-smbus

To install cv2, see [opencv_notes](opencv_notes.txt).


## Runtime Dependencies

Additional packages required to run the atles\_box/atles\_remote software:

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

