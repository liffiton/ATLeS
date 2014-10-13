
thickness = 0.25;

width = 20;
length = 20;
height = 10;

// width and height of tank base plate
base_width = width/4;
base_height = 1;

// height of side supports
//side_support_height = height/2; // full side walls
side_support_height = 2;

// amount faces extend past each other at corners
overhang = 1;

// for minor corrections
epsilon = 0.01;

vert_faces();
side_supports();
tank_base();

module vert_faces() {
	difference() {
		union() {
			vert_face(x=0);
			vert_face(x=length);
		}
		side_support_base(clearance=0.1, height_scale=0.5);
		side_support_top(clearance=0.1, height_scale=0.5);
	}
}

module vert_face(x) {
	translate([x-thickness/2,0,0])
		cube([thickness,width,height]);
}

module tank_base(clearance=0) {
	translate([thickness,0,base_height])
	difference() {
		cube([base_width, length, thickness + clearance]);
		tank_base_cutouts(clearance);
		translate([0,length-overhang-thickness/2,0])
			tank_base_cutouts(clearance);
	}
}

module tank_base_cutouts(clearance=0) {
	cube([base_width/8, overhang+thickness/2, thickness+clearance]);
	translate([3*base_width/8,0,0])
		cube([base_width/4, overhang+thickness/2, thickness+clearance]);
	translate([7*base_width/8,0,0])
		cube([base_width/8+epsilon, overhang+thickness/2, thickness+clearance]);
}

module side_supports() {
	difference() {
		union() {
			side_support_base();
			side_support_top();
		}
		vert_faces();
		tank_base(clearance=0.1);
	}
}

module side_support_top(clearance=0, height_scale=1) {
	translate([0,0,height])
	side_support_base(clearance=clearance, height_scale=-height_scale);
}

module side_support_base(clearance=0, height_scale=1) {
	scale([1,1,height_scale])
		union() {
			side_support(y=overhang, clearance=clearance);
			side_support(y=width-overhang, clearance=clearance);
		}
}

module side_support(y, clearance) {
	translate([-overhang,y-thickness/2-clearance/2,0])
		cube([length+overhang*2, thickness+clearance, side_support_height+clearance]);
}