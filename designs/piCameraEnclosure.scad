// Modified from: https://github.com/luisibanez/ShapesFor3DPrinting/tree/master/OpenSCA

module piCameraEnclosure() 
{

	module piCameraBackCoverBevel(clearance) {
		c = clearance;
		hw = ( 25 / 2 ) + c;
		he = hw + 1.5 + c;
		polyhedron(
			points = [
				[ hw, -15-c, -1-c ],
				[ hw,  15+c, -1-c ], 
				[ hw,  15+c,  1 ], 
				[ hw, -15-c,  1 ],
				[ he, -15-c, -1-c ],
				[ he,  15+c, -1-c ] 
				], 
			faces = [
				[ 5, 1, 0, 4],
				[ 4, 0, 3 ],
				[ 2, 1, 5 ],
				[ 5, 4, 3, 2],
				[ 0, 1, 2, 3],
			]
		);
	}

	module piCameraBackCoverBevels(clearance) {
		union() {
			piCameraBackCoverBevel(clearance);
			mirror([1,0,0])
				piCameraBackCoverBevel(clearance);
		}
	}

	module piCameraBackCover(clearance=0, indent=true) {
		c = 2*clearance;
		translate([0,-5.5,9])
			difference() {
				union() {
					piCameraBackCoverBevels(clearance);
					cube(size=[25+c,30+c,2+c],center=true);
				}
				translate([0,12,0])
					cube(size=[20.5-c,7,3],center=true);
				if (indent)
					translate([0,-12,1.5])
					rotate([0,90,0])
						cylinder(r=1, h=40, center=true, $fn=20);
			}
	}

	module cableOpening() {
		translate([0,14,8.1])
			cube(size=[17,12,4],center=true);
	}

	module chipOpening() {
		clearance = 0.5;
		c = 2 * clearance;
		translate([0,-9.5,5])
			cube(size=[8+c,10+c,4],center=true);
	}

	module lensOpening() {
		clearance = 0.5;
		c = 2 * clearance;
		translate([0,0,2.5])
			cube(size=[8+c,8+c,5+c], center=true);
	}

	module boardOpening() {
		clearance = 0.2;
		c = 2 * clearance;
		translate([0,-3,7.5])
			cube(size=[25+c,24+c,5+clearance], center=true);
	}

	module cameraFrame() {
		translate([0,-0.5,5])
			cube(size=[40,40,10], center=true);
	}

	module roundedCorner(radius) {
		translate([-radius, -radius, 0])
		difference() {
			translate([0,0,-50])
				cube(size=[radius+0.1,radius+0.1,100]);
			cylinder(h=100, r=radius, $fn=50, center=true);
		}
   }

   module cornerRounding(radius) {
		// vertical corners
		translate([20,19.5,0])
			roundedCorner(radius);
		translate([-20,19.5,0])
		rotate([0,0,90])
			roundedCorner(radius);
		translate([-20,-20.5,0])
		rotate([0,0,180])
			roundedCorner(radius);
		translate([20,-20.5,0])
		rotate([0,0,-90])
			roundedCorner(radius);

		// top corners
		translate([-20,0,10])
		rotate([0,-90,0])
		rotate([90,0,0])
			roundedCorner(radius/2);
		translate([20,0,10])
		rotate([90,0,0])
			roundedCorner(radius/2);
   }

	module piCameraAdapter() {
		difference() {
			cameraFrame();
			boardOpening();
			chipOpening();
			cableOpening();
			lensOpening();
			cornerRounding(radius=8);
			piCameraBackCover(clearance=0.3, indent=false);
		}
	}

	union() {
		piCameraAdapter();
		// Comment out translate to see
		// back cover in place.
		translate([40,5,-8])
			piCameraBackCover();
	}
}

piCameraEnclosure();
