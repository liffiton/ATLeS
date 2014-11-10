// Dimensions are in mm
height = 10;
mincut = 0.05;
maxcut = 0.3;
cutstep = 0.025;
cutshift = maxcut + 0.5;
numcuts = ((maxcut - mincut) / cutstep + 1);
width = cutshift * numcuts;

projection(cut=false) testobj();

module testobj() {
    difference () {
        cube([width, height, 0.1]);
        for (i = [0 : numcuts]) {
            translate([cutshift * (i+1), 0, -50])
                cube([mincut + cutstep*i, height/2, 100]);
        }
    }
}
