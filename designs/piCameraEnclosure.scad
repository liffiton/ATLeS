// Adapted from: https://github.com/luisibanez/ShapesFor3DPrinting/tree/master/OpenSCA

// For case
width  = 35;  // x
length = 35;  // y
height = 11;  // z

// For camera cover
flex_adapter_width = 22;   // measures 21mm, but w/ a nominal 22mm opening it was still too tight.
cover_width = 27;
cover_height = 2;

// For rounded corners
radius1 = 8;
radius2 = 4;

piCameraAdapter();
// Comment out translate to see
// back cover in place.
translate([width,4,-(height-cover_height)])
    piCameraBackCover();


/////////////////////////////////////////////////////////////////////////////////////
// Modules
//

module piCameraBackCoverBevel(length, clearance) {
    c = clearance;
    hh = cover_height / 2;
    hw = ( cover_width / 2 ) + c;
    he = hw + 1.5 + c;
    l = length / 2;
    polyhedron(
        points = [
            [ hw, -l-c, -hh-c ],
            [ hw,  l+c, -hh-c ], 
            [ hw,  l+c, hh ], 
            [ hw, -l-c, hh ],
            [ he, -l-c, -hh-c ],
            [ he,  l+c, -hh-c ] 
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

module piCameraBackCover(for_subtraction=false) {
    indent = ! for_subtraction;
    clearance = for_subtraction ? 0.25 : 0;
    c = 2*clearance;
    cov_l = length-8;
    difference() {
        translate([0,-5,height-cover_height/2])
        difference() {
            translate([0,1,0])
            union() {
                cube(size=[cover_width+c,cov_l+c,cover_height+c],center=true);
                piCameraBackCoverBevel(cov_l, clearance);
                mirror([1,0,0])
                    piCameraBackCoverBevel(cov_l, clearance);
            }
            translate([0,15,0])
                cube(size=[flex_adapter_width-c,15,100],center=true);
            if (indent)
                translate([0,8-length/2,cover_height/2+0.5])
                rotate([0,90,0])
                    cylinder(r=1, h=cover_width-4, center=true, $fn=20);
        }
        if (! for_subtraction) {
            cornerRounding();
        }
    }
}

module cableOpening() {
    w = 17;
    d = 12;
    h = 100;
    translate([-w/2,2+d/2,height-4+0.1])
        cube(size=[w,d,h]);
}

module chipOpening() {
    clearance = 0.5;
    c = 2 * clearance;
    w = 8+c;
    d = 10+c;
    h = 100;
    translate([-w/2, -9.5-d/2, height-7])
        cube(size=[w,d,h]);
}

module ledOpening() {
    clearance = 0.5;
    c = 2 * clearance;
    w = 4+c;
    d = 3+c;
    h = 100;
    translate([7-w/2, -11-d/2, height-6])
        cube(size=[w,d,h]);
}

module lensOpening() {
    clearance = 0.5;
    c = 2 * clearance;
    w = 8+c;
    d = 8+c;
    h = 100;
    translate([-w/2,-d/2,-1])
        cube(size=[w,d,h]);
}

module boardOpening() {
    clearance = 0.3;
    c = 2 * clearance;
    w = 25+c;
    d = 24+c;
    h = 100;
    translate([-w/2,-d/2 - 3, height-5])
        cube(size=[w,d,h]);
}

module cameraFrame() {
    translate([0,0,height/2])
        cube(size=[width,length,height], center=true);
}

module roundedCorner(r) {
    translate([-r, -r, 0])
    difference() {
        translate([0,0,-50])
            cube(size=[r+0.1,r+0.1,100]);
        cylinder(h=100, r=r, $fn=50, center=true);
    }
}

module cornerRounding() {
    // vertical corners
    translate([width/2,length/2,0])
        roundedCorner(radius1);
    translate([-width/2,length/2,0])
    rotate([0,0,90])
        roundedCorner(radius1);
    translate([-width/2,-length/2,0])
    rotate([0,0,180])
        roundedCorner(radius1);
    translate([width/2,-length/2,0])
    rotate([0,0,-90])
        roundedCorner(radius1);

    // top corners
    translate([-width/2,0,height])
    rotate([0,-90,0])
    rotate([90,0,0])
        roundedCorner(radius2);
    translate([width/2,0,height])
    rotate([90,0,0])
        roundedCorner(radius2);
}

module piCameraAdapter() {
    difference() {
        cameraFrame();
        boardOpening();
        chipOpening();
        ledOpening();
        cableOpening();
        lensOpening();
        cornerRounding();
        piCameraBackCover(for_subtraction=true);
    }
}
