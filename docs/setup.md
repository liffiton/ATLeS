---
title: "Documentation: System Integration & Setup"
---

# Installation / Setup

A complete ATLeS installation consists of an ATLeS server and one or more ATLeS boxes on the same network as the server.

## Network Setup

Only the server needs to be accessible to other machines.  For security purposes, the boxes should ideally be on an isolated private network that connects only the boxes and the server, but this is not strictly required.  
The minimum requirement for the software to work correctly (finding and registering boxes in the server interface) is that the server and the boxes are on the same subnet / broadcast domain.

The Raspberry Pi systems controlling the boxes should not be considered strongly secured, and separating them from other networks is ideal.  One way to achieve this security and separation is to install the server on a machine with two network interfaces: one connects to the regular campus/business network, while the other connects to a separate switch along with all of the ATLeS boxes.

### Without a Separate Server

The server software *can* run on a Raspberry Pi, even one installed in and controlling an ATLeS box, and so it is possible to create a working system with even just a single Raspberry Pi.  This is **not recommended** due to security, performance, and stability issues that may arise.  However, it can provide a quick, relatively simple way to prototype or demonstrate ATLeS.

## ATLeS Server

The server software has been tested under Debian Linux and Cygwin.  It should work on any recent Linux distribution, and it may run on other platforms as well.

To install the server software, first clone the ATLeS repository:

    git clone https://github.com/liffiton/ATLeS.git

Required Python packages can be installed using pip (`pip3` is used as ATLeS is written for Python 3).  If you need to install pip, refer to [these instructions](https://pip.pypa.io/en/stable/installing/).

    cd ATLeS/src
    pip3 install --user -U -r requirements_web.txt

The `--user` flag installs the required packages for the current user only.  Alternatively, you can install them and run ATLeS within a [virtual environment](https://docs.python.org/3/library/venv.html) or install them systemwide by omitting `--user` and adding `sudo` before the `pip3` command.

If pip installs the required packages successfully, you should be able to run the server:

    ./atles_web.py

By default, it will start serving the web interface on port 8080 (configurable via the `--port` command line option), and it will be accessible by pointing a web browser to http://1.2.3.4:8080/, where 1.2.3.4 is replaced with the IP address of the server.

## ATLeS Box

### Installing the Software

The easiest way to install the required software on a Raspberry Pi for a new
ATLeS Box is to burn (write) a pre-configured image onto a MicroSD card.  Disk
images are available as versioned releases on Github:
[https://github.com/liffiton/ATLeS/releases](https://github.com/liffiton/ATLeS/releases).
Download a disk image and extract the .img file.  We recommend using
[Etcher](https://etcher.io/) to burn the image to a MicroSD card.

Alternatively, follow the [Manual Box Software Setup](box_sw_manual_install) instructions to install all needed software from scratch.

### Setting Up a Newly-Cloned Raspberry Pi

If using a provided pre-configured image to install the software, a few additional steps are required.

Login to a newly-installed Raspberry Pi as pi/fishypi.

Run `sudo raspi-config` and:

  1. Expand filesystem to fit (depending on the image you used, this may have been done automatically already)

  2. Set hostname (suggestion: name boxes sequentially and label each box with its hostname -- this is how they will be identified in the web interface)

Exit the configuration software and reboot.

After rebooting the box, there is one more step to register the box on the
server.  From the **server**, run:

    ATLeS/install/setup_box.sh [box hostname or IP]

You will need to provide a password to log in to the box (default: fishypi),
and it will then setup the box to run the `atles_remote.py` software at boot.

Now, if the box is connected to the same network as the server, the box should
appear in the web interface automatically.
