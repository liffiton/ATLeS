
// Set thickness to account for thickness of material
// PLUS needed clearance for cuts into which material should fit.
thickness = 0.25;

width = 20;   // x
depth = 20;   // y
height = 10;  // z

// width and height of tank base plate
base_width = width/5;
base_height = 1;
light_bar_width = 1;
light_height = height-1;

// height of side supports
//side_support_height = height/2; // full side walls
side_support_height = 2;

// amount faces extend past each other at corners
overhang = 1;

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
	translate([x-thickness/2,0,0])
		cube([thickness,depth,height]);
}

module tank_base() {
	translate([thickness,0,base_height])
	difference() {
		cube([base_width, depth, thickness]);
		cutouts(3,base_width);
		translate([0,depth-overhang-thickness/2,0])
			cutouts(3,base_width);
	}
}

module light_bar() {
	translate([thickness+base_width-light_bar_width,0,light_height])
	difference() {
		cube([light_bar_width, depth, thickness]);
		cutouts(2,light_bar_width);
		translate([0,depth-overhang-thickness/2,0])
			cutouts(2,light_bar_width);
	}
}

module cutouts(num, width) {
    w = width / ((num-1) * 2);
    for (i = [0 : num-1]) {
        translate([-w/2 + i*2*w,0,0])
            cube([w, overhang+thickness/2, thickness]);
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
			side_support(y=overhang);
			side_support(y=depth-overhang);
		}
}

module side_support(y) {
	translate([-overhang,y-thickness/2,0])
		cube([width+overhang*2, thickness, side_support_height]);
}
