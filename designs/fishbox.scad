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
width = 400;   // x
depth = 300;   // y
height = 180;  // z

// tank base plate
base_width = width-thickness*2;
base_height = 10;

// light bar
light_bar_width = 30;
light_pos_x = 50;
light_height = height-10;

// height of side supports
side_support_height = height/2; // full side walls
//side_support_height = 20;

// amount faces extend past each other at corners
overhang = 10;

// amount horizontal support bars extend past side supports
outset = overhang/2;

// components to include (comment out unwanted)
vert_faces();
side_supports();
tank_base();
light_bar();

//////////////////////////////////////////////////////////////////
// Module definitions
//

module vert_faces() {
	difference() {
		union() {
			vert_face(x=0);
			vert_face(x=width);
		}
		side_support_base(height_scale=0.5);
		side_support_top(height_scale=0.5);
	}
}

module vert_face(x) {
	translate([x-thickness/2,-overhang,0])
		cube([thickness,depth+overhang*2,height]);
}

module tank_base() {
	translate([thickness,-outset,base_height])
	difference() {
		cube([base_width, depth+outset*2, thickness]);
		cutouts(5,base_width,outset,far_side=false);
        cutouts(5,base_width,outset,far_side=true);
	}
}

module light_bar() {
	translate([light_pos_x,-outset,light_height])
	difference() {
		cube([light_bar_width, depth+outset*2, thickness]);
		cutouts(2,light_bar_width,outset,far_side=false);
        cutouts(2,light_bar_width,outset,far_side=true);
	}
}

module cutouts(num, width, outset, far_side=False) {
    w = width / ((num-1) * 2);
    y = far_side ? depth+outset-thickness/2 : 0;
    for (i = [0 : num-1]) {
        translate([-w/2 + i*2*w,y,0])
            cube([w, outset+thickness/2, thickness]);
    }
}

module side_supports() {
	difference() {
		union() {
			side_support_base();
			side_support_top();
		}
		vert_faces();
		tank_base();
        light_bar();
	}
}

module side_support_top(height_scale=1) {
	translate([0,0,height])
        side_support_base(height_scale=-height_scale);
}

module side_support_base(height_scale=1) {
	scale([1,1,height_scale])
		union() {
			side_support(y=0);
			side_support(y=depth);
		}
}

module side_support(y) {
	translate([-overhang,y-thickness/2,0])
		cube([width+overhang*2, thickness, side_support_height]);
}
