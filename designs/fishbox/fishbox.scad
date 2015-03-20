// fishbox.scad
//  - Enclosure design for zebrafish Skinner box
//  
//  Author: Mark Liffiton
//  Date: Oct, 2014 - Jan, 2015
//
//  Units are mm

// Set thickness to account for thickness of material
// PLUS needed clearance for cuts into which material should fit.

// 0.100" Acrylic:
window_thickness = 2.4;  // 2.4mm = 0.094" (looks good based on cut test piece for acrylic slotting into itself)

// 1/8" Hardboard:
thickness = 3.1;
    // 2.8mm = 0.110"
    //   * looked good based on cut test piece for hardboard slotting into hardboard
    //   * 2015-03-06: Hanging supports didn't fit into cutouts (or did only with lots of force)
    // 3.1mm for some breathing room

// Interior box dimensions
// The variables are used below to control placement of **centerpoints** centerpoints of walls,
// so material thickness is added to account for that.
width = 290 + thickness;    // x = 29cm wall-to-wall
depth = 348 + thickness;    // y = 34.8cm to accomodate 34.8cm tank length
i_height = 190 + thickness; // z = 19cm to accomodate 16cm tank height plus light holder, plus cover
                            // (i_height because 'height' is used for height of entire box)

// amount faces extend past each other at corners
overhang = 15;

// amount horizontal support tabs extend past side supports (technically, it will go this distance minus thickness/2)
outset = thickness+2;

// tank base plate
base_height = overhang/2;

// create height var to account for raised base
height = i_height + base_height;

// light bar
light_bar_width = 30;
light_pos_x = 50;
light_height = height-thickness*2-8;

// hanging support thickness and drop (distance it "sits down" after in place)
support_w = 10;
support_drop = support_w/2;

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
} else if (DXF_LIGHT_BAR) {
    projection() light_bar();
} else if (DXF_CAMERA_SUPPORT) {
    projection() rotate(a=[90,0,0]) camera_supports(justone=true);
} else if (DXF_RPI_SUPPORT) {
    projection() rotate(a=[90,0,0]) rpi_support();
}
else {
    // 3D model
    // components to include (comment out unwanted)
    vert_face(x=0);      // "near face, transparent for monitor
    vert_face(x=width);  // "far" face, with camera, rpi, etc.
    side(y=0);
    side(y=depth);
    tank_base();
    light_bar();
    camera_supports(x=width, y=depth/2, z=height/2);
    rpi_support(x=width, y=rpi_ypos-10, z=height/2);
    mock_rpi(x=width, y=rpi_ypos, z=height/2);
    top_cover();
}

//////////////////////////////////////////////////////////////////
// Module definitions
//

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
        camera_supports(x=width+thickness*2, y=depth/2, z=height/2+support_drop, round=false);
        rpi_support(x=width+thickness*2, y=rpi_ypos-10, z=height/2+support_drop, round=false);
        wire_opening();
        // CAUTION: OpenSCAD won't let me make a projection of vert_face(x=0)
        //   if tank_base is put after side(y=depth) here... bug.  :(
        tank_base();
        top_cover();
        side(y=0);
        side(y=depth);
        translate([x-thickness/2, -overhang, 0]) {
            translate([0, depth+overhang+thickness/2, 3/4*height])
                rounded_truncation(width=overhang-thickness/2, up=true);
            translate([0, 0, 3/4*height])
                rounded_truncation(width=overhang-thickness/2, up=true);
        }
    }
}

module vert_face_base(x, face_thickness=thickness) {
    translate([x-face_thickness/2, -overhang, 0])
        cube([face_thickness,depth+overhang*2,height]);
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
        cube([thickness*2,10,10], center=true);
}

module camera_supports(x, y, z, justone=false, round=true) {
    spacing = 20;
    out = 11;
    up = 36;
    hanging_support(x, y + spacing/2, z, out, up, round=round);
    if (!justone) {
        hanging_support(x, y - spacing/2, z, out, up, round=round);
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
    color("Grey", alpha=0.5)
    translate([-outset,-outset,height-thickness])
    difference() {
        cube([width+outset*2,depth+outset*2,thickness]);
        cutouts(5,width-thickness,outset,rot=0,trans=[width/2+outset,0,0]);
        cutouts(5,width-thickness,outset,rot=180,trans=[width/2+outset,depth+outset*2,0]);
        cutouts(5,depth-thickness,outset,rot=-90,trans=[0,depth/2+outset,0]);
        cutouts(5,depth-thickness,outset,rot=90,trans=[width+outset*2,depth/2+outset,0]);
    }
}

module tank_base() {
    translate([-outset,thickness/2,base_height])
    difference() {
        cube([width+outset*2, depth-thickness, thickness]);
        cutouts(5,depth,outset,rot=-90,trans=[0,(depth-thickness)/2,0]);
        cutouts(5,depth,outset,rot=90,trans=[width+outset*2,(depth-thickness)/2,0]);
    }
}

module light_bar_opening() {
    // A wider opening, so the bar can slide out of the way of placing or removing the fish tank
    translate([light_pos_x-light_bar_width/4, -outset, light_height])
        cube([light_bar_width*2, depth+outset*2, thickness]);
}

module light_bar() {
    translate([light_pos_x-light_bar_width/2, -outset, light_height])
    difference() {
        cube([light_bar_width, depth+outset*2, thickness]);
        cutouts(2,light_bar_width,outset,rot=0,trans=[light_bar_width/2,0,0]);
        cutouts(2,light_bar_width,outset,rot=180,trans=[light_bar_width/2,depth+outset*2,0]);
    }
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
    translate([width, rpi_ypos-35, overhang+20])
    scale([1,2,1])
    rotate(a=[0,90,0])
        cylinder(d=12, h=thickness+epsilon, center=true);
}

module side(y=0) {
    difference() {
        side_base(y);
        scale([1,1,0.5])
            vert_face_base(0, window_thickness);
        scale([1,1,0.5])
            vert_face_base(width);
        light_bar_opening();
        top_cover();
    }
}

module side_base(y) {
    translate([-overhang,y-thickness/2,overhang/2])
    difference() {
        cube([width+overhang*2, thickness, height-overhang/2]);
        translate([width+overhang+thickness/2, 0, 0])
            rounded_truncation(width=overhang-thickness/2, up=false, rot=[0,0,-90]);
        translate([0, 0, 0])
            rounded_truncation(width=overhang-window_thickness/2, up=false, rot=[0,0,-90]);
    }
}

module mock_rpi(x, y, z) {
    color("Blue", alpha=0.5)
    translate([x+thickness, y, z])
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
