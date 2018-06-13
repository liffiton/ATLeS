---
title: "Building an ATLeS Box Enclosure"
---

# Building an ATLeS Box Enclosure

The `designs` folder in the ATLeS repository contains source files for nearly all of the parts required to build an ATLeS box enclosure.  In the `designs/box/box_structure.scad` is an [OpenSCAD](http://www.openscad.org/) 3D model of the enclosure.

DXF files suitable for laser-cutting are provided in `designs/dist`.  They can be re-created from the OpenSCAD source using `make` (requires OpenSCAD).

The enclosure was designed to be laser cut from 1/8" [hardboard](https://en.wikipedia.org/wiki/Hardboard).  Other sheet materials suitable for laser cutting (e.g. plywood or acrylic) may work with small modifications to the design to account for different material thickness.

## Build Walkthrough

All of the DXF files in `designs/dist` should be laser cut out of opaque material *except* `tank_support.dxf`, which is meant to be clear acrylic (so the infrared illumination below it reaches the tank above).  The `tank_baffle*.dxf` and `tank_lid*.dxf` files are not part of the enclosure, but rather they are designed to be used in a particular model of fish tank.


### Step 1
To start, slot the bottom sheet `bottom.dxf` into the slots on the two end pieces `end1.dxf` and `end2.dxf`:

{:.center}
[![Build step 1](imgs/box_structure_1.png){:width="500px"}](imgs/box_structure_1.png)<br>
Build step 1

### Step 2
Next, slide the two side pieces `side1.dxf` and `side2.dxf` into the slots on the edges of the end pieces to form a box:

{:.center}
[![Build step 2](imgs/box_structure_2.png){:width="500px"}](imgs/box_structure_2.png)<br>
Build step 2

The above image also shows the placement of the clear acrylic tank support pieces.  The two thin pieces are on the bottom, with room between for the strip of infrared lights, and the larger piece covers them and provides a platform for the fish tank.

### Step 3
The mask piece `mask.dxf` slides in from the top, interfacing with the two sides:

{:.center}
[![Build step 3](imgs/box_structure_3.png){:width="500px"}](imgs/box_structure_3.png)<br>
Build step 3

### Step 4
The two top pieces `top.dxf` fit into place on top of the box (they are translucent here but should be opaque in reality), and the support bracket for the Rasberry Pi holds it in place as shown:

{:.center}
[![Build step 4](imgs/box_structure_4.png){:width="500px"}](imgs/box_structure_4.png)<br>
Build step 4

The camera mounts using M2 standoffs and screws.  The circular hole in the back piece is for mounting a 2.5mm DC jack for power, and the wider, elliptical hole is for passing wires through from the Raspberry Pi to the electronics inside.

### Step 5 (only if stacking)
Enclosures can be stacked up to three high, with each offset to the rear from the one below to allow access to load fish tanks into each.  In this case, a rear support piece can be added at the vertical slit on the rear of any box whose back is now unsupported:

{:.center}
[![Build step 5](imgs/box_structure_5.png){:width="500px"}](imgs/box_structure_5.png)<br>
Build step 5 (optional)

Adjust the length of the support piece as needed to reach the surface below.
