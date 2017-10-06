---
title: (Manual) Box Software Setup
---

Most people will not need to use the following instructions.  They are provided
for anyone who wants to set up the ATLeS box software environment themselves.
The easiest way to install and use the software is to install a provided OS
image.  The following installation steps require that you are comfortable
working in a Linux development environment.

# Installing ATLeS Software

A common setup will install `atles_web.py` on a server (it has been tested
under Linux and Cygwin thus far), while `atles_remote.py` will run on one or
more Raspberry Pi nodes in the experiment boxes.  When installing on a
Raspberry Pi, start with a clean install of
[Raspbian](https://www.raspberrypi.org/downloads/raspbian/).

The following instructions cover installing the software on a Raspberry Pi, and
they were developed and tested on a clean install of Raspbian Stretch Lite
(2017-09-07).

## Software Dependencies

Before installing the software, install the required tools and libraries (many
may already be installed depending on your base system):

    sudo apt install build-essential pkg-config python3-dev python3-pip libpng-dev libfreetype6-dev git rsync

## Downloading ATLeS Software

Clone the ATLeS repository:

    git clone https://github.com/liffiton/ATLeS.git

The ATLeS software will now be in a folder named `ATLeS`.  The following
commands assume you have changed into that directory.

### atles\_remote.py and atles\_box.py

The software that runs on each box to control experiments and connects back to
the server depends on several Python packages that can be installed via pip and
two that can be installed separately.

Install the first set of packages by running:

    sudo pip3 install --user -U -r src/requirements_remote.txt

We install using sudo here so that the libraries are available systemwide, as `atles_remote.py` will be run as root (to be able to control the PWM output).

The packages that are installed separately are `cv2` (OpenCV) and `smbus` (for
reading sensors values).

To install smbus:

    sudo apt install python-smbus

To install cv2, see [opencv_notes](opencv_notes.md).

### atles\_web.py

The server software is normally run on a system separate from the Raspberry
Pi(s) (see [setup](setup)).  However, it can be installed on a Raspberry Pi
alongside the `atles-remote.py`/`atles_box.py` programs for testing or
prototyping purposes.

Install the Python packages required for `atles_web.py` by running:

    pip3 install --user -U -r src/requirements_web.txt

If you want to install matplotlib on an older RPi, you may have to work around
an issue with pip.  A standard pip install of matplotlib can fail on a stock
RPi with a memory error.  To work around this, install it without using the
cache (thanks to:
[http://stackoverflow.com/a/31526029](http://stackoverflow.com/a/31526029)):

    pip3 install --user --no-cache-dir matplotlib

Re-run the earlier pip command after installing matplotlib this way, if this
was necessary.

 
## Runtime Dependencies

Both the camera and i2c need to be enabled using raspi-config.  Run `sudo
raspi-config` and enable both (i2c is under "advanced options").

To use the camera via v4l, the `bcm2835-v4l2` module must be loaded.  For the
i2c interface (for sensors), the `i2c-dev` module must be loaded.  To have the
modules loaded automatically on boot, add each to `/etc/modules`, one per line:

    bcm2835-v4l2
    i2c-dev

Alternatively, modprobe can be used to load them manually at any time:

    sudo modprobe bcm2835-v4l2
    sudo modprobe i2c-dev

