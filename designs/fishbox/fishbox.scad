// fishbox.scad
//  - Enclosure design for zebrafish Skinner box
//  
//  Author: Mark Liffiton
//  Date: Oct, 2014 - Nov, 2015
//
//  Units are mm

// Set thickness to account for thickness of material
// PLUS needed clearance for cuts into which material should fit.

// 0.100" Acrylic:
acrylic_thickness = 2.4;
    // 2.4mm = 0.094" (looks good based on cut test piece for acrylic slotting into itself)

// 1/8" Hardboard:
hardboard_thickness = 3.2;
    // 2.8mm = 0.110"
    //   * looked good based on cut test piece for hardboard slotting into hardboard
    //   * 2015-03-06: Hanging supports didn't fit into cutouts (or did only with lots of force)
    // 3.1mm for some breathing room
    //   * 2016-02-26: Still tighter than is ideal for sliding parts together.
    // 3.2mm for just a smidge more...

// Assign materials: window/back wall and everything else
//window_thickness = acrylic_thickness;
window_thickness = hardboard_thickness;
thickness = hardboard_thickness;

// Interior box dimensions
// The variables are used below to control placement of **centerpoints** centerpoints of walls,
// so material thickness is added to account for that.
width = 290 + thickness;    // x = 29cm wall-to-wall
depth = 348 + thickness;    // y = 34.8cm to accomodate 34.8cm tank length
i_height = 180 + thickness; // z = 18cm to accomodate 16cm tank height plus cover
                            // (i_height because 'height' is used for height of entire box)

// amount faces extend past each other at corners
overhang = 15;

// amount horizontal support tabs extend past side supports (technically, it will go this distance minus thickness/2)
outset = thickness+2;

// tank base plate
base_height = overhang/2;

// create height var to account for raised base
height = i_height + base_height;

// hanging support thickness and drop (distance it "sits down" after in place)
support_w = 10;
support_drop = support_w/2;

// useful tank measurements
tank_width = 70;
tank_foot_offset_left = 105;
tank_foot_offset_right = 101;

// x-position of mask piece inside box
mask_loc = tank_width + thickness;  // center-to-center
// dimensions for mask view opening
view_opening_left = 65;
view_opening_right = 78;
view_opening_width = depth-thickness - view_opening_left - view_opening_right;
view_opening_bottom = 24;
view_opening_height = 96;

// camera mounting measurements
camera_hole_diameter = 1.7;       // bolts are m2; 2mm nominal, 1.9mm actual, and a bit less for the beam width
camera_hole_horiz_offset = 21/2;  // 21mm between mounting holes, horizontally (so half that away from the camera center
camera_hole_vert_offset = 12.5;   // 12.5mm between mounting holes, vertically (one set on the camera center, one set up that much from center)

// position of rpi and related parts
rpi_ypos = depth/2 + 60;

// for slight offsets/tweaks
epsilon = 1;

// set precision of all arcs/spheres/cylinders/etc.
$fn = 50;

// vars to control projection for DXF export (see makefile)
if (DXF_TOP) {
    projection() top_cover();
} else if (DXF_BOTTOM) {
    projection() tank_base();
} else if (DXF_SIDE1) {
    projection() rotate(a=[90,0,0]) side(y=0);
} else if (DXF_SIDE2) {
    projection() rotate(a=[90,0,0]) side(y=depth);
} else if (DXF_END1) {
    projection() rotate(a=[0,90,0]) vert_face(x=0);
} else if (DXF_END2) {
    projection() rotate(a=[0,90,0]) vert_face(x=width);
} else if (DXF_MASK) {
    projection() rotate(a=[0,90,0]) mask(x=mask_loc);
} else if (DXF_TANK_SUPPORT) {
    projection() tank_support_layer1();
    projection() translate([tank_width+thickness,0,0]) tank_support_layer2();
    projection() translate([(tank_width+thickness)*2,0,0]) tank_support_layer3();
} else if (DXF_RPI_SUPPORT) {
    projection() rotate(a=[90,0,0]) rpi_support();
}
else {
    // 3D model
    // components to include (comment out unwanted)
    vert_face(x=0);      // "near face, transparent for monitor
    vert_face(x=width);  // "far" face, with camera, rpi, etc.
    mask(x=mask_loc);
    side(y=0);
    side(y=depth);
    tank_base();
    tank_support();
    rpi_support(x=width, y=rpi_ypos-10, z=height/2);
    mock_rpi(x=width, y=rpi_ypos, z=height/2);
    top_cover();
}

//////////////////////////////////////////////////////////////////
// Module definitions
//

module mask(x) {
    difference() {
        vert_face_base(x, top_offset=thickness, bottom_offset=base_height-thickness);
        side(y=0);
        side(y=depth);
        translate([x-thickness/2, -overhang, 0]) {
            translate([0, 0, 0])
                rounded_truncation(width=overhang-thickness/2, up=false);
            translate([0, depth+overhang+thickness/2, 0])
                rounded_truncation(width=overhang-thickness/2, up=false);
        }
        // opening for tank view
        translate([0,view_opening_left+thickness/2, view_opening_bottom+base_height+thickness/2])
            cube([width, view_opening_width, view_opening_height]);
        // opening for wires
        translate([0, depth-thickness/2, base_height+thickness])
        rotate(a=[0,90,0])
            cylinder(r=10, h=width);
        // tabs for rigidity w/ bottom panel
        cutouts(4,depth-thickness,outset*2,rot=[-90,0,90],trans=[x+thickness/2,depth/2,base_height+thickness/2]);
    }
}

module vert_face(x=0) {
    difference() {
        if (x == 0) {
            vert_face_base(0, window_thickness);
        }
        else {
            vert_face_base(x);
        }
        camera_opening();
        // round=false so we get the full width of the piece in the cutout, not reduced because we hit the rounded corner
        rpi_support(x=width+thickness*2, y=rpi_ypos-10, z=height/2+support_drop, round=false);
        wire_opening();
        // CAUTION: OpenSCAD won't let me make a projection of vert_face(x=0)
        //   if tank_base is put after side(y=depth) here... bug.  :(
        tank_base();
        top_cover();
        side(y=0);
        side(y=depth);
        translate([x-thickness/2, -overhang, 0]) {
            translate([0, depth+overhang+thickness/2, 0])
                rounded_truncation(width=overhang-thickness/2, up=false);
            translate([0, 0, 0])
                rounded_truncation(width=overhang-thickness/2, up=false);
        }
    }
}

module vert_face_base(x, face_thickness=thickness, top_offset=0, bottom_offset=0) {
    translate([x-face_thickness/2, -overhang, bottom_offset])
        cube([face_thickness,depth+overhang*2,height-top_offset-bottom_offset]);
}

module rounded_truncation(width, up, rot=[0,0,0]) {
    truncation_height=height/4;
    rotate(a=rot)
    difference() {
        translate([-50,-epsilon,0])
            cube([100, width+2*epsilon, truncation_height]);
        if (up) {
            translate([-50, width/2, 0])
            rotate(a=[0, 90, 0])
                cylinder(d=width, h=100);
        }
        else {
            translate([-50, width/2, truncation_height])
            rotate(a=[0, 90, 0])
                cylinder(d=width, h=100);
        }
    }
}

module camera_opening() {
    translate([width, depth/2, height/2])
    union() {
        cube([thickness*2,10,10], center=true);
        translate([0, camera_hole_horiz_offset, 0])
        rotate(a=[0, 90, 0])
            cylinder(d=camera_hole_diameter, h=100, center=true);
        translate([0, -camera_hole_horiz_offset, 0])
        rotate(a=[0, 90, 0])
            cylinder(d=camera_hole_diameter, h=100, center=true);
        translate([0, camera_hole_horiz_offset, camera_hole_vert_offset])
        rotate(a=[0, 90, 0])
            cylinder(d=camera_hole_diameter, h=100, center=true);
        translate([0, -camera_hole_horiz_offset, camera_hole_vert_offset])
        rotate(a=[0, 90, 0])
            cylinder(d=camera_hole_diameter, h=100, center=true);
    }
}

module rpi_support(x, y, z, round=true) {
    hanging_support(x, y, z, out=4, up=85, round=round);
}

module hanging_support(x, y, z, out, up, round=true) {
    inner_w = out+thickness;
    inner_h = up;
    color("Red", alpha=0.5)
    translate([x,y,z])
    // push inner opening up against vert face
    translate([out/2,0,0])
    difference() {
        if (round) {
            rounded_rect(inner_w+support_w*2, thickness, inner_h+support_w*2, center=true, radius=support_w);
        }
        else {
            cube([inner_w+support_w*2, thickness, inner_h+support_w*2], center=true);
        }
        // cutout for object
        cube([inner_w, thickness*2, inner_h], center=true);
        // cutout for passing through vertface
        translate([-(inner_w/2+support_w/2),0,-support_drop/2])
            cube([support_w+2*epsilon, thickness*2, inner_h-support_drop], center=true);
        // bottom cutout
        translate([-out/2,0,-(inner_h/2+support_w-support_drop/2)])
            cube([thickness, thickness*2, support_drop], center=true);
    }
}

// rounded corners in x,z directions
module rounded_rect(x,y,z, center, radius) {
    difference() {
        cube([x,y,z], center);

        translate([x/2-radius, 50, z/2-radius])
        rotate(a=[90,0,0])
        difference() {
            cube([radius,radius,100]);
            cylinder(r=radius, h=100);
        }
        translate([-x/2+radius, 50, z/2-radius])
        rotate(a=[90,-90,0])
        difference() {
            cube([radius,radius,100]);
            cylinder(r=radius, h=100);
        }
        translate([x/2-radius, 50, -z/2+radius])
        rotate(a=[90,90,0])
        difference() {
            cube([radius,radius,100]);
            cylinder(r=radius, h=100);
        }
        translate([-x/2+radius, 50, -z/2+radius])
        rotate(a=[90,180,0])
        difference() {
            cube([radius,radius,100]);
            cylinder(r=radius, h=100);
        }
    }
}

module top_cover() {
    // width1 = main cover ; width2 = tank section cover
    width1 = width - mask_loc - thickness/2;
    width2 = mask_loc - thickness/2;
    color("Grey", alpha=0.5)
    union() {
        // back piece (over empty space)
        translate([0,-outset,height-thickness])
        difference() {
            translate([mask_loc,0,0])
                cube([width1+thickness+outset,depth+outset*2,thickness]);
            cutouts(4,width1,outset,rot=0,trans=[width1/2+mask_loc,0,0]);
            cutouts(4,width1,outset,rot=180,trans=[width1/2+mask_loc,depth+outset*2,0]);
            cutouts(5,depth-thickness,outset,rot=90,trans=[width+outset,depth/2+outset,0]);
        }
        // front piece (over tank)
        translate([-outset-thickness/2,-overhang,height-thickness])
        difference() {
            cube([width2+thickness+outset,depth+overhang*2,thickness]);
            cutouts(5,depth-thickness,outset,rot=90,trans=[outset+thickness/2,depth/2+overhang,0]);
        }
    }
}

module tank_base() {
    difference() {
        translate([-outset,thickness/2,base_height])
            difference() {
                cube([width+outset*2, depth-thickness, thickness]);
                cutouts(5,depth,outset,rot=-90,trans=[0,(depth-thickness)/2,0]);
                cutouts(5,depth,outset,rot=90,trans=[width+outset*2,(depth-thickness)/2,0]);
            }
        mask(x=mask_loc);
    }
}

module tank_support() {
    translate([thickness/2, thickness/2, base_height+thickness])
    union() {
        tank_support_layer1();
        color("Grey", alpha=0.5)
            tank_support_layer2();
/*
        color("Grey", alpha=0.5)
            tank_support_layer3();
*/
    }
}
// Two strips of hardboard on either side of LED strip
module tank_support_layer1() {
    // front bottom strip, w/ space for wires
    translate([0, 0, 0])
        cube([tank_width/3, depth-thickness, thickness]);
    // back bottom strip, full-depth
    translate([2*tank_width/3, 0, 0])
        cube([tank_width/3, depth-thickness-20, thickness]);
}
// Clear acrylic over LED strip
module tank_support_layer2() {
    translate([0, 0, thickness])
    difference() {
        cube([tank_width, depth-thickness, thickness]);
        translate([tank_width/2, depth-tank_width/2, 0])
            cylinder(d=25, h=100, center=true);
    }
}
// Clear acrylic end blocks to prevent tank shifting / seat it in correct location
// [Currently unused -- 2016-02-26]
module tank_support_layer3() {
    translate([0, 0, thickness*2])
        cube([tank_width, tank_foot_offset_right, thickness]);
    translate([0, depth-thickness-tank_foot_offset_left, thickness*2])
        cube([tank_width, tank_foot_offset_left, thickness]);
}

module cutouts(num, width, outset, rot, trans) {
    w = width / ((num-1) * 2);
    translate(trans)
    rotate([0,0,1], a=rot)
    for (i = [0 : num-1]) {
        translate([-width/2 - w/2 + i*2*w, -thickness/2, -thickness/2])
            cube([w, outset+thickness, thickness*2]);
    }
}

module wire_opening() {
    translate([width, rpi_ypos+20, overhang+20])
    scale([1,2,1])
    rotate(a=[0,90,0])
        cylinder(d=12, h=thickness+epsilon, center=true);
}

module side(y=0) {
    difference() {
        side_base(y);
        translate([0,0,height/2])
        scale([1,1,0.5])
            vert_face_base(x=mask_loc);
        translate([0,0,height/2])
        scale([1,1,0.5])
            vert_face_base(0, window_thickness);
        translate([0,0,height/2])
        scale([1,1,0.5])
            vert_face_base(width);
        top_cover();
    }
}

module side_base(y) {
    translate([-overhang,y-thickness/2,0])
    difference() {
        cube([width+overhang*2, thickness, height]);
        translate([width+overhang+thickness/2, 0, 3/4*height])
            rounded_truncation(width=overhang-thickness/2, up=true, rot=[0,0,-90]);
        translate([0, 0, 3/4*height])
            rounded_truncation(width=overhang-window_thickness/2, up=true, rot=[0,0,-90]);
    }
}

module mock_rpi(x, y, z) {
    color("Blue", alpha=0.5)
    translate([x+thickness/2, y, z])
        rotate(a=[0,-90,180])
            translate([-85/2, -56/2, 0])
                union() {
                    cube([85, 56, 2]);
                    // USB1
                    translate([67, 41, 2])
                        cube([20, 12, 12]);
                    // USB2
                    translate([67, 23, 2])
                        cube([20, 12, 12]);
                }
}
