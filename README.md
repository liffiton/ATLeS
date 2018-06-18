# ATLeS: Automated Tracking and Learning System

The goal of the ATLeS project is to create an inexpensive, open-source system for automated, high-throughput, realtime observation and conditioning experiments.  Zebrafish, *danio rerio*, are the target organism for the initial design.

ATLeS consists of one or more ATLeS boxes, each of which can run an automated experiment on a single organism at a time, and a separate server that provides a combined interface for managing and controlling all of the boxes and their experiments in one place.
Each box uses an inexpensive [Raspberry Pi](https://www.raspberrypi.org/) as its "brain," an infrared-sensitive camera as its "eyes," and inexpensive materials for the structure.
A central server can connect to boxes over a network (ethernet or wifi) to control and manage them via a web interface.
The server software is written in Python, and it runs under Linux, OS X, or Windows.

Please visit the main [ATLeS website](https://liffiton.github.io/ATLeS) or look in the ``docs`` folder for more details and documentation.

## Authors

ATLeS was created by [Mark Liffiton](https://www.iwu.edu/~mliffito/) and [Brad Sheese](https://www.iwu.edu/psychology/faculty/BradSheese.html) at [Illinois Wesleyan University](https://www.iwu.edu/).

## Open-Source Licenses

Each part of the ATLeS project is licensed under one of two open-source licenses, depending on what type of material it is.  See [``docs/licenses.md``](docs/licenses.md) for details.
