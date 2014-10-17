// fishbox.scad
//  - Enclosure design for zebrafish Skinner box
//  
//  Author: Mark Liffiton
//  Date: Oct, 2014
//
//  Units are mm

// Set thickness to account for thickness of material
// PLUS needed clearance for cuts into which material should fit.
thickness = 3;

// Interior box dimensions (from centerpoints of walls, so actual dimension is minus material thickness)
width = 400;     // x
depth = 300;     // y
i_height = 180;  // z  (i_height because 'height' is used for height of entire box)

// amount faces extend past each other at corners
overhang = 20;

// amount horizontal support bars extend past side supports
outset = overhang/2;

// tank base plate
base_width = width-thickness*2;
base_height = overhang;

// create height var to account for raised base
height = i_height + base_height;

// light bar
light_bar_width = 30;
light_pos_x = 50;
light_height = height-10;

// for slight offsets/tweaks
epsilon = 1;

// components to include (comment out unwanted)
vert_faces();
sides();
tank_base();
light_bar();
camera_supports(x=width, y=depth/2, z=height/2, spacing=20);
top_cover();

//////////////////////////////////////////////////////////////////
// Module definitions
//

module vert_faces() {
	difference() {
		union() {
			vert_face(x=0);
            difference() {
                vert_face(x=width);
                camera_opening();
                camera_supports(x=width+thickness*2, y=depth/2, z=height/2+10, spacing=20);
            }
		}
		sides_base(height_scale=0.5);
	}
}

module vert_face(x) {
	translate([x-thickness/2,-overhang,overhang])
		cube([thickness,depth+overhang*2,height-overhang]);
}

module camera_opening() {
    translate([width, depth/2, height/2])
        cube([thickness*2,10,10], center=true);
}

module camera_supports(x, y, z, spacing) {
    camera_support(x, y + spacing/2, z);
    camera_support(x, y - spacing/2, z);
}

module camera_support(x, y, z) {
    inner_w = 20;
    inner_h = 30;
    inner_offset = 5;
    translate([x,y,z])
    // shift down to center on camera opening
    translate([0,0,-inner_offset])
    // push inner opening up against vert face
    translate([inner_w/2,0,0])
    difference() {
        cube([inner_w+20, thickness, inner_h+30], center=true);
        // cutout for camera
        translate([0,0,inner_offset])
            cube([inner_w, thickness*2, inner_h], center=true);
        // cutout for passing through vertface
        translate([-10-epsilon,0,0])
            cube([inner_w, thickness*2, inner_h-10], center=true);
        // bottom cutout
        translate([-inner_w/2,0,-25])
            cube([thickness, thickness*2, 10], center=true);
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
	translate([thickness,-outset,base_height])
	difference() {
		cube([base_width, depth+outset*2, thickness]);
		cutouts(5,base_width,outset,rot=0,trans=[base_width/2,0,0]);
		cutouts(5,base_width,outset,rot=180,trans=[base_width/2,depth+outset*2,0]);
	}
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

module sides() {
	difference() {
        sides_base();
		vert_faces();
		tank_base();
        light_bar();
        light_wire_opening();
        top_cover();
	}
}

module sides_base(height_scale=1) {
	scale([1,1,height_scale])
		union() {
			side(y=0);
			side(y=depth);
		}
}

module side(y) {
	translate([-overhang,y-thickness/2,0])
		cube([width+overhang*2, thickness, height]);
}
