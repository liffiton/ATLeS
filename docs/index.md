---
title: Automated Tracking and Learning System
---

The goal of the ATLeS project is to create an inexpensive, open-source system for automated, high-throughput, realtime observation and conditioning experiments.  Zebrafish, *danio rerio*, are the target organism for the initial design.

ATLeS consists of one or more ATLeS boxes, each of which can run an automated experiment on a single organism at a time, and a separate server that provides a combined interface for managing and controlling all of the boxes and their experiments in one place.
Each box uses an inexpensive [Raspberry Pi](https://www.raspberrypi.org/) as its "brain," an infrared-sensitive camera as its "eyes," and inexpensive materials for the structure.
A central server can connect to boxes over a network (ethernet or wifi) to control and manage them via a web interface.
The server software is written in Python, and it runs under Linux, OS X, or Windows.

# Make Your Own

All source files, including code and complete designs for physical parts, are available in the [ATLeS Github repository](https://www.github.com/liffiton/ATLeS).

Building a single ATLeS box costs roughly $100 and requires some assembly and wiring.  The enclosure is designed to be laser cut from hardboard or similar flat, rigid materials.  Using the provided design files, you can either laser-cut the pieces yourself or order them from an online laser-cutting service.

Follow the ~~[illustrated walkthrough](TBD)~~ *[coming soon]* in the [documentation](docs.md) to guide the assembly and software installation.

# Use It

After the boxes are assembled and the software is installed, run ``src/atles_web.py`` and point a browser to ``http://[hostname]:8080/``.  As you turn on boxes, they should become visible in the main web interface.

# Adapt It

Because the entire system is open-source, from the code to the physical design, you can modify and adapt the system to suit your needs.  Modify the enclosure to accomodate a different style of tank.  Tweak the software to perform a different analysis.  Or just take a component out to use in your own system.  See [Licenses](licenses) for details.
