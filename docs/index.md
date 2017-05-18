---
layout: page
title: TBD
---

The goal of the [whatever] project is to create an inexpensive, open-source system for automated, high-throughput, realtime observation and conditioning experiments of small model organisms.  Zebrafish, <i>danio rerio</i>, are the target organism for the initial design.

The [whatever] system consists of one or more [whatever] Boxes and optionally a separate server that provides a combined interface for managing and controlling several boxes and their experiments in one place.
Each box uses an inexpensive [Raspberry Pi](https://www.raspberrypi.org/) as its "brains," an infrared-sensitive camera as its "eyes," and inexpensive materials for the structure.
The optional but recommended central server can connect to boxes over a network (ethernet or wifi) to control and manage them.
The server software is written in Python, and it runs under Linux, OS X, or Windows.

## Make Your Own

All source files, including code and complete designs for physical parts, are available in the [whatever Github repository](https://www.github.com/liffiton/whatever).

Building a single [whatever] box costs roughly $100 (?) and requires some assembly and wiring.  The enclosure is designed to be laser cut from hardboard or similar flat, rigid materials.  You can either laser-cut the pieces yourself with the provided design files or order pre-cut pieces from an online laser-cutting service.

Follow the [illustrated walkthrough](something) in our documentation to guide the assembly.

## Adapt It

Because the entire system is open-source, from the code to the physical design, you can modify and adapt the system to suit your needs.  Modify the enclosure to accomodate a different style of tank.  Tweak the software to perform a different analysis.  Or just take a component out to use if your own system.  See [Licenses](licenses) for details.

## Documentation

*In Progress:* The documentation is not yet fully written nor organized, and for now, the following notes are available:
 * [Box software installation](box_sw_install)
 * [Box software usage notes](box_sw_notes)

For developers:
 * [(Manual) box software setup](box_sw_manual_install)
 * [Box software image cloning](box_sw_cloning)
