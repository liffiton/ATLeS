// fishbox.scad
//  - Enclosure design for zebrafish Skinner box
//  
//  Author: Mark Liffiton
//  Date: Oct, 2014 - Jan, 2015
//
//  Units are mm

// Set thickness to account for thickness of material
// PLUS needed clearance for cuts into which material should fit.
thickness = 1.8;  // 1.8mm = 0.07" (looks good based on cut test piece)

// Interior box dimensions (from centerpoints of walls, so actual dimension is minus material thickness)
width = 290;    // x = 29cm wall-to-wall
depth = 350;    // y = 35cm to accomodate 34.5cm tank length
i_height = 180+thickness;
                // z = 18cm to accomodate 16cm tank height plus light holder, plus cover
                // (i_height because 'height' is used for height of entire box)

// amount faces extend past each other at corners
overhang = 20;

// amount horizontal support bars extend past side supports
outset = overhang/2;

// tank base plate
base_depth = depth-thickness*2;
base_height = overhang;

// create height var to account for raised base
height = i_height + base_height;

// light bar
light_bar_width = 30;
light_pos_x = 50;
light_height = height-thickness*2-10;

// for slight offsets/tweaks
epsilon = 1;

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
}
else {
    // 3D model
    // components to include (comment out unwanted)
    vert_face(x=0);
    vert_face(x=width);
    side(y=0);
    side(y=depth);
    tank_base();
    light_bar();
    // camera supports (z -5 to center on camera opening)
    hanging_supports(x=width, y=depth/2, z=height/2-5, out=20, up=30, spacing=20);
    // rpi support
    hanging_support(x=width, y=depth/4+9, z=height/2, out=3, up=85);
    mock_rpi(x=width, y=depth/4, z=height/2);
    top_cover();
}

//////////////////////////////////////////////////////////////////
// Module definitions
//

module vert_face(x=0) {
    difference() {
        vert_face_base(x);
        camera_opening();
        // camera supports (z -5 to center on camera opening)
        hanging_supports(x=width+thickness, y=depth/2, z=height/2-5+10, out=20, up=30, spacing=20);
        // rpi supports
        hanging_support(x=width+thickness, y=depth/4+9, z=height/2+10, out=3, up=85);
        side(y=0);
        side(y=depth);
        tank_base();
    }
}

module vert_face_base(x) {
    translate([x-thickness/2,-overhang, 0])
        cube([thickness,depth+overhang*2,height]);
}

module camera_opening() {
    translate([width, depth/2, height/2])
        cube([thickness*2,10,10], center=true);
}

module hanging_supports(x, y, z, out, up, spacing) {
    hanging_support(x, y + spacing/2, z, out, up);
    hanging_support(x, y - spacing/2, z, out, up);
}

module hanging_support(x, y, z, out, up) {
    inner_w = out+thickness;
    inner_h = up;
    cutout_w = 10;
    translate([x,y,z])
    // push inner opening up against vert face
    translate([inner_w/2,0,0])
    difference() {
        cube([inner_w+cutout_w*2, thickness, inner_h+cutout_w*3], center=true);
        // cutout for object
        cube([inner_w, thickness*2, inner_h], center=true);
        // cutout for passing through vertface
        translate([-(inner_w/2+cutout_w/2),0,-cutout_w/2])
            cube([cutout_w+2*epsilon, thickness*2, inner_h-10], center=true);
        // bottom cutout
        translate([-inner_w/2,0,-(inner_h/2+cutout_w)])
            cube([thickness, thickness*2, cutout_w], center=true);
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
    translate([-outset,thickness,base_height])
    difference() {
        cube([width+outset*2, base_depth, thickness]);
        cutouts(5,depth,outset,rot=-90,trans=[0,base_depth/2,0]);
        cutouts(5,depth,outset,rot=90,trans=[width+outset*2,base_depth/2,0]);
    }
}

module light_bar_opening() {
    // A wider opening, so the bar can slide out of the way of placing or removing the fish tank
    translate([light_pos_x, -outset, light_height])
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
        translate([-width/2 - w/2 + i*2*w, -thickness/2, -epsilon])
            cube([w, outset+thickness, thickness+epsilon*2]);
    }
}

module light_wire_opening() {
    translate([light_pos_x, 0, light_height-10])
    scale([2,1,1])
    rotate(v=[1,0,0], a=90)
        cylinder(d=10, h=thickness+epsilon, center=true);
}

module side(y=0) {
    difference() {
        side_base(y);
        scale([1,1,0.5])
            vert_face_base(x=0);
        scale([1,1,0.5])
            vert_face_base(x=width);
        light_bar_opening();
        light_wire_opening();
        top_cover();
    }
}

module side_base(y) {
    translate([-overhang,y-thickness/2,overhang/2])
        cube([width+overhang*2, thickness, height-overhang/2]);
}

module mock_rpi(x, y, z) {
    translate([x+thickness, y, z])
        rotate(v=[0,1,0], a=90)
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
