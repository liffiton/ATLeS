
thickness = 0.5;

width = 20;
length = 20;
height = 10;

vert_faces();
side_supports();

module vert_faces() {
	difference() {
		union() {
			vert_face(x=0);
			vert_face(x=length);
		}
		scale([1,1,0.5]) {
			side_support_base(clearance=0.1);
		}
	}
}

module vert_face(x) {
	translate([x-thickness/2,0,0])
		cube([thickness,width,height]);
}

module side_supports() {
	difference() {
		side_support_base();
		vert_faces();
	}
}

module side_support_base(clearance=0) {
	union() {
		side_support(y=2, clearance=clearance);
		side_support(y=width-2, clearance=clearance);
	}
}

module side_support(y, clearance) {
	overhang = 1;
	height = 2;
	translate([-overhang,y-thickness/2-clearance/2,0])
		cube([length+overhang*2, thickness+clearance, height+clearance]);
}