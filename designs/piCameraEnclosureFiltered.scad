// Modified from: https://github.com/luisibanez/ShapesFor3DPrinting/tree/master/OpenSCA

module piCameraEnclosure() 
{
	function r_from_dia(d) = d / 2;
	function midValue(a,b) = ( a + b ) / 2;

	union() {
		piCameraAdapter();
		translate([50,0,-8])
			piCameraBackCover(0.1);
	}

	module piCameraBackCoverBevel(clearance) {
		c = clearance;
		hw = ( 25 / 2 ) + c;
		he = hw + 1.0;
		polyhedron
			(points = [
				[ hw, -15, -1 ],
				[ hw,  15, -1 ], 
				[ hw,  15,  1 ], 
				[ hw, -15,  1 ],
				[ he, -15, -1 ],
				[ he,  15, -1 ] 
				], 
			triangles = [
				[ 0, 1, 4 ],
				[ 1, 5, 4 ],
				[ 0, 4, 3 ],
				[ 1, 2, 5 ],
				[ 2, 3, 4 ],
				[ 2, 4, 5 ],
				[ 0, 2, 1 ],
				[ 0, 3, 2 ]
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

	module piCameraBackCover(clearance) {
		c = 2*clearance;
		translate([0,-5.5,24])
			union() {
				piCameraBackCoverBevels(clearance);
				difference() {
					cube(size=[25+c,30,2],center=true);
					translate([0,12,0])
						cube(size=[20,7,2],center=true);
				}
			}
	}

	module cableOpening() {
		translate([0,14,3])
			cube(size=[17,12,4],center=true);
	}

	module chipOpening() {
		clearance = 0.5;
		c = 2 * clearance;
		translate([0,-9.5,0])
			cube(size=[8+c,10+c,4],center=true);
	}

	module lensOpening() {
		clearance = 0.5;
		c = 2 * clearance;
		translate([0,0,-2.5])
			cube(size=[8+c,8+c,5], center=true);
	}

	module boardOpening() {
		clearance = 0.5;
		c = 2 * clearance;
		translate([0,-3,2.5])
			cube(size=[25+c,24+c,5], center=true);
	}

	module filterSlot() {
		translate([0,0,-3])
		rotate(a = 90, v = [0,1,0])
		linear_extrude(height = 100, center = true) {
			polygon(
				points = [
					[0,-10],[10,0],[0,10]
				],
				path = [0,1,2,0]
			);
		}
	}

	module cameraFrame() {
		translate([0,-0.5,0])
			cube(size=[40,40,10], center=true);
	}

	module piCameraAdapter() {
		difference() {
			translate([0,0,20])
				difference() {
					cameraFrame();
					boardOpening();
					lensOpening();
					cableOpening();
					chipOpening();
					filterSlot();
				}
			piCameraBackCover(0.5);
		}
	}

}

piCameraEnclosure();
