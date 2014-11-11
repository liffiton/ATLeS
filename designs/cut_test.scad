// Dimensions are in mm by default; scale by 25.4 to get inches
height = 10;
mincut = 0.02;
maxcut = 0.3;
cutstep = 0.02;
cutshift = maxcut + 0.5;
numcuts = ((maxcut - mincut) / cutstep) + 1;
width = cutshift * (numcuts+1);

projection(cut=false) testobj();
//testobj();

module testobj() {
    difference () {
        union() {
            cube([width, height, 0.1]);
            // testing tab
            translate([width, 2*height/3, 0])
                cube([0.5, 1, 0.1]);
        }

        // slot cuts
        for (i = [0 : numcuts]) {
            translate([cutshift * (i+1), 0, -50])
                cube([mincut + cutstep*i, height/2, 100]);
        }

        // tab cuts
        for (i = [0 : 5]) {
            translate([2*(i+1) - 1, height-0.5, -50])
                cube([1-(i*0.01), 1, 100]);
        }
    }
}
