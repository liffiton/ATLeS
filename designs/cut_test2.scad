// Dimensions are in mm by default
height = 2.5;    // 0.1" = 2.54mm
mincut = 2;
maxcut = 3.6;      // 0.125" = 3.175mm, so get some cuts above that
cutstep = 0.2;
cutshift = maxcut * 2;
cutlength = 50;  // 5cm
length = cutlength + 2*maxcut;
numcuts = ((maxcut - mincut) / cutstep) + 1;
width = cutshift * (numcuts+1);

projection(cut=false) testobj();
//testobj();

module testobj() {
    difference () {
        cube([width, length, height]);

        // slot cuts
        for (i = [0 : numcuts-1]) {
            translate([cutshift * (i+0.5), 0, -50])
                cube([mincut + cutstep*i, cutlength, 100]);
        }
    }
}
