// Raspberry Pi Case
// Hans Harder 2012
//
// Warning: this is based on the Beta board dimensions...
//          so production models can be slightly different
//          for instance SD card holder height and USB socket dimensions
//
// Since all connectors stick out, case is split on HDMI height
// so the power and sdcard holder goes in first and then the pcb drops into place.
//
// v2: Adapted version after some suggestions from David...
//     removed feet, made both surface flat
// v3: Added fliptop option and smooth the corners of the box
// v4: Different levels of case split (make it 3d printable, thx David)
//     Looks strange but it fits...
//     Added frame mode (so no bottom and top deck)
//     Moved screw locations due to split and added some support structures
//     Unsure about 2nd screw location in combination with GPIO pins
// v5  relocated a lot of code in modules
//     SDslot location was not calculated correctly
// v6  Added pcb drawing
//     Added colors
//     Cut out better so there is no debris around
//     DRAwvars and options seperated, so it is easier to do 1 part
//     Make a low as possible case, let USB stick out
// v7  PCB options
//     Low level case optimisations
//     SD card location alterations
// v8  adapted pcb dimensions, board is really 56mm width
//     adapted support studs, moved some due to component location
//     components locations adapted
// v9  Added logo in seperate dxf file
//     Option added to put logo in middle or using whole deck
//     beautified code, kr style
// v10 Added logosunken and bottomsupport structures
//     Bottom supports are located where no components are located
//       so the pcb is not only supported from the sides
//     Well got my case, so based on what I see I changed:
//     case split level changed, should be better when printed on a reprap
//     Removed screwholes (far to small) for fastening top and added some more studs
//     Made frontstud a little thicker
// v11 Different splitlevel (more simple) on back
//     keep a little margin on back split, so that top and bottom always fit
//     added openlogo option
// v12 Different component locations/sizes
//     keep a little margin on component holes
//     pcbsize to 57.0 x 86.0   (actual it is 56.17 x 85.0)
//     made casestuds wider and added 2 minor holes for self tapping screws
// v13 skip this one.... :)
// v14 Production board measurements...
//	   small differences, sometimes components are soldered differently
//     keep more space
//     should fit like a glove...
// v15 moved the rca and snd a bit to get them more centered
//     Thanks to lincomatic at Thingiverse
//     Added option for GPIO side hole in bottom or top
//     Added showing GPIO pins with component drawing
//
// All parts are draw as default just disable the ones you don't want
DRAWfull        = 0;
DRAWtop         = 1;
DRAWbottom      = 1;
DRAWpcb         = 0;

GPIOHOLE        = 2;        // GPIO opening in :  1=bottom   2=top
GPIOsize        = 2;        // define height of gpiohole

// select how the case should look like
topframe    = false;        // if false, underneath values determines how
topholes    = true;
ledholes    = true;
// ---- holes sizes
holeofs=6;
holesiz=3;
holestep=8;
noholes=7;
holelen=30;
topmiddle   = false;

bottomframe = false;        // if false, underneath values determines how
bottomholes = false;
bottomscrew = false;
bottomsupport = false;         // Added extra support locations for pcb
bottomclick   = true;
bottompcb    = false;		    // just a pcb holder without a top

box_thickness = 2.0;            // minimum = 1.0
inside_h      = 12.5;           // 12.1 = lowprofile    16.5 is full height
pcb_h         = 5.6;            // height needed for SD holder and solder points of pcb
//pcb_h         = box_thickness+3.5;    // height needed for SD holder and solder points of pcb
// 4.1 = no deck, box_thickness+3.5 is with deck

// just some colors to see the difference
CASEcolor="Maroon";
CONNcolor="Silver";

// Define Raspberry Pi pcb dimensions in mm
inside_l = 86.0;                //85.00 is largest length reported, so a bit room on each side
inside_w = 57.2;                //56.17 is largest width  reported, so a bit room on each side
pcb_thickness = 1.7;

// Coordinates based on RJ45 corner = 0,0,0
// pcb connectors and locations. Based on Beta Board measurements of Gert and a real RPi

// Connectors
Crj45_x=2.0;			 //2.0
Crj45_y=-1;
Crj45_w=16.4;			// 15.4
Crj45_d=21.5;           //21.8
Crj45_h=13.8;

Cusb_x=24.5;            // 23.9
Cusb_y=-7.7;
Cusb_w=13.9;            // 13.3
Cusb_d=19.0;			// 17.2
Cusb_h=16.0;

Cpwr_x=3.25;				// 3.5 3.6
Cpwr_y=80.9;
Cpwr_w=8.8;				// 7.8 7.6
Cpwr_d=5.6;
Cpwr_h=2.6;

Csd_x=16.7;
Csd_y=inside_l-24.0;            // 30 mm is the length of a  sdcard
Csd_w=27.8;
Csd_d=29.0;
Csd_h=3.4;                  // under pcb

Chdmi_x=-1.2;
Chdmi_y=32.0;               // 32.4  if 15.1
Chdmi_w=11.4;
Chdmi_d=17.8;				  // 15.7 15.3
Chdmi_h=6.4;

Csnd_x=inside_w - 11.4;
Csnd_y=16.0;
Csnd_w=11.4;
Csnd_d=10.0;
Csnd_h=10.5;
Csnd_r=6.7;
Csnd_z=3.0;
Csnd_l=3.4;

Crca_x=inside_w - 10.0 - 2.1;
Crca_y=34.2;                // 34.6 was 35.2
Crca_w=10.0;
Crca_d=10.4;                 // 9.8
Crca_h=13.0;
Crca_r=8.6;
Crca_z=4;
Crca_l=10;                  // wild guess



pcb_c = pcb_h + pcb_thickness;            // component height
casesplit = pcb_c + Chdmi_h;              // split case at top of hdmi connector
echo("casesplit=",casesplit);
echo("case dimensions: w=",box_w," l=",box_l," h=",box_h);

// side stud sizes for supporting pcb
stud_w = 2;
stud_l = 4;

// calculate box size
box_l  = inside_l + (box_thickness * 2);
box_w  = inside_w + (box_thickness * 2);
box_h  = pcb_c + (pcb_thickness * 2) + inside_h;
box_w1 = box_thickness;
box_w2 = box_w - box_thickness;
box_l1 = box_thickness;
box_l2 = box_l - box_thickness;
box_wc = box_w / 2;                 // center width
box_lc = box_l / 2;                 // center length
box_t2 = box_thickness / 2.0;           // half box_thickness
middle = true;
// rounded corners
corner_radius = box_thickness*2;



// count no of items to draw
DRAWtotal = DRAWfull + DRAWtop + DRAWbottom;

// ====================================================== DRAW items
// if one  draw it centered
if (DRAWtotal == 1) {
    translate(v = [ -box_w/2, -box_l / 2, 0]) {
        if (DRAWfull ) {
           draw_case(0,1);
           translate(v=[0,0,0.2]) draw_case(1,0);
        }
        if (DRAWtop   ) {
            rotate(a=[0,180,0]) translate(v=[-box_w,0,-box_h]) draw_case(0,1);
        }
        if (DRAWbottom) draw_case(1,0);
    }
} else {
// draw each one on there one location
    if (DRAWfull)   {
        translate(v = [ box_w+20, -box_l / 2, 0]) {
            draw_case(1,0);
            translate(v=[0,0,0.2]) draw_case(0,1);
        }
    }
    if (DRAWbottom) {
        translate(v = [ 5, 5, 0]) draw_case(1,0);
    }
    if (DRAWtop)    {
        translate(v = [ - 5,  5, box_h])  rotate(a=[0,180,0]) draw_case(0,1);
    }
}

// ======================================================= END of draw
// Module sections

module make_deckholes(no,w,d,step) {
for ( i = [0 : 1 : no - 1] ) {
        translate(v=[w/2,(i*step)+(step/2),box_thickness/2]) cube([w,d, box_thickness+18], center=true);
    }
}


// create a deck or insert
module make_deck(w,d,z,hole_no,hole_size,hole_step) {
    hole_w=(w - 12) / 2;      // change 12 for middle piece size
    ofs1=4;
    ofs2=w - ofs1 - hole_w;
    hole_ofs= ((d - hole_no*hole_step) / 2) - box_thickness/2;
    translate(v = [(box_w-w)/2, (box_l-d)/2,z]) {
        color(CASEcolor) {
            echo("deck : z=",z," w=",w+0.01," d=",d+0.01);
            difference() {
                cube([w, d, box_thickness], center = false);
                if (top && holes && hole_size>0) {
                    translate(v=[-1,hole_ofs+holeofs,-0.1]) make_deckholes(noholes,holelen,holesiz,holestep);
                    translate(v=[w/2-2,hole_ofs+holeofs,-0.1]) make_deckholes(noholes,holelen,holesiz,holestep);
                }
                if (screwholes) {
                    // --- 2x screw holes in bottom for mounting
                    translate(v = [w/2 - 4, 10-4, -1]) cube([8, 3, 5], center = false);
                    translate(v = [w/2 - 4, 10-3, -1]) cylinder(r=3, h=8, $fn=100, center=true);
                    // 2nd screw hole
                    translate(v = [w/2 - 3, d - 10 +3, -1]) cube([8, 3, 5], center = false);
                    translate(v = [w/2 + 4, d - 10 +4, -1]) cylinder(r=3, h=8, $fn=100);
                    if (!holes) {
                        // middle screw hole
                        translate(v = [w/2 - 4, d/2    , -1]) cube([8, 2, 5], center = false);
                        translate(v = [w/2 - 4, d/2 + 1, -1]) cylinder(r=2, h=8, $fn=100);
                    }
                }
                if (holes && !top) {
                    translate(v=[(w-hole_w)/2,holeofs,-0.1]) make_deckholes(noholes,hole_w,holesiz,holestep);
                }
                if (top && ledholes) {
						translate([w-8,3,-0.1])
	                    cube([5,11,20]);
                }
            }
            color(CASEcolor) {
                if (top && holes) {
                    translate(v = [w/2-box_thickness,12,0]) cube([4,d-13, box_thickness], center = false);
                }
                if (middle) {
                    // --- solid area for sticker
                    translate(v = [w/2-10,d/2-5-box_thickness/2,0]) {
                        cube([20,20, box_thickness], center = false);
                    }
                }
            }
        }
    }
}

module rounded_corner(x,y,rx,ry,cx,cy) {
    translate(v = [x, y, -1]) {
        difference() {
            translate(v=[rx,ry,0])    cube([corner_radius,corner_radius,box_h+2], center=false);
            translate(v=[cx, cy, -1]) cylinder(r=corner_radius, h=box_h+2, $fn=100);
        }
    }
}


module make_topcomponents(alpha=1) {
    color(CONNcolor, alpha=alpha) translate(v=[box_w1,box_l1,pcb_c]) {
        translate(v=[Crj45_x,Crj45_y,0]) cube([Crj45_w,Crj45_d,Crj45_h],center=false);
        translate(v=[Cusb_x,Cusb_y,0])   cube([Cusb_w,Cusb_d,Cusb_h],center=false);
        translate(v=[Cpwr_x,Cpwr_y,0])   cube([Cpwr_w,Cpwr_d,Cpwr_h],center=false);
        translate(v=[Chdmi_x,Chdmi_y,0]) cube([Chdmi_w,Chdmi_d,Chdmi_h],center=false);

        //SND
        translate(v=[Csnd_x,Csnd_y,0]) cube([Csnd_w+0.1,Csnd_d,Csnd_h],center=false);
        translate(v=[Csnd_x+Csnd_w,Csnd_y+Csnd_d/2,Csnd_z+Csnd_r/2]) rotate(a=90,v=[0,1,0]) cylinder(r=Csnd_r/2, h=Csnd_l, $fn=100);

        //RCA
        translate(v=[Crca_x,Crca_y,0]) cube([Crca_w+0.2,Crca_d,Crca_h],center=false);
        translate(v=[Crca_x+Crca_w,Crca_y+Crca_d/2,Crca_z+Crca_r/2]) rotate(a=90,v=[0,1,0]) cylinder(r=Crca_r/2, h=Crca_l+0.1, $fn=100);
    }
    for ( i = [0 : 1 : 12] ) {
        color("black", alpha=alpha) translate(v=[box_w2-6.6,box_l2-1-34+(i*2.54),pcb_c]) cube([5.08,2.53,2.5]);
        color("Gainsboro", alpha=alpha) translate(v=[box_w2-6.6+0.97,box_l2-1-34+(i*2.54)+0.95,pcb_c-3])  cube([0.6,0.6,11.5]);
        color("Gainsboro", alpha=alpha) translate(v=[box_w2-6.6+3.61,box_l2-1-34+(i*2.54)+0.95,pcb_c-3])  cube([0.6,0.6,11.5]);

    }
}

module make_connholes() {
    // =================================== cut outs, offset from 0,0
    //RJ45:    2mm offset, 15.5mm width, 13.1mm height
    set_cutout(box_w1+Crj45_x,box_l1+Crj45_y-3,pcb_c,   Crj45_w+0.1,Crj45_d+3,Crj45_h);
    //usb:  23.9mm offset, 13.3mm width, 15.4mm height
    set_cutout(box_w1+Cusb_x,box_l1+Cusb_y,pcb_c,   Cusb_w,Cusb_d,Cusb_h+0.1);

    //power: 3.4mm offset,    8mm width,    3mm height
    set_cutout(box_w1+Cpwr_x,box_l1+Cpwr_y,pcb_c,   Cpwr_w,Cpwr_d+4,Cpwr_h+0.01);
    //sd:   15mm offset,   28mm width,    3.5mm height under pcb
    if (pcb_h >= (Csd_h+1.5) ) {
        set_cutout(box_w1+Csd_x-0.3,box_l2-28,pcb_h-Csd_h,Csd_w+0.6,box_thickness+30,Csd_h+0.1);
    } else {
        set_cutout(box_w1+Csd_x-0.3,box_l2-32,pcb_h-20,Csd_w+0.6,40,20.01);
    }
    //HDMI: 32.9mm offset,  15.3mm width,   6.3mm height
    set_cutoutv(box_w1+Chdmi_x-3,box_l1+Chdmi_y,pcb_c,    Chdmi_w+3.1,Chdmi_d,Chdmi_h+0.1);

    // snd:   14mm offset,  12mm width,   8.2 mm height
    set_cutout(box_w1+Csnd_x,box_l1+Csnd_y,pcb_c+2,    Csnd_w+7,Csnd_d,Csnd_h-2);

    // RCA:   35mm offset,  10mm width     10mm height
    translate(v=[box_w1+Crca_x+Crca_w,box_l1+Crca_y+Crca_d/2,pcb_c+Crca_z+Crca_r/2]) {
        rotate(a=90,v=[0,1,0]) cylinder(r=Crca_r/2+1, h=Crca_l, $fn=100);
    }
    translate(v=[box_w1+Crca_x+Crca_w,box_l1+Crca_y+(Crca_d-Crca_r)/2-1,pcb_c+Crca_z-1]) {
        cube([5,Crca_r+2,Crca_r/2+1]);
    }
}

module make_pcb(alpha=1) {
    translate(v=[box_w1,box_l1,pcb_h]) {
        color("darkgreen", alpha=alpha) cube([inside_w,inside_l,pcb_thickness], center=false);
    }
    color(CONNcolor, alpha=alpha) {
        translate(v=[box_w1+Csd_x,box_l1+Csd_y,pcb_h-Csd_h]) cube([Csd_w,Csd_d,Csd_h],center=false);
    }
    make_topcomponents(alpha=alpha);
}

// put extra supports on free spaces, used beta board image
module make_supports() {
    if (!bottomframe) {
        translate(v=[box_w1+10 ,box_l1+28,0.1]) cube([3, 2,pcb_h-0.1]);
        translate(v=[box_w2-7.5,box_l1+28,0.1]) cube([3, 2,pcb_h-0.1]);

        translate(v=[box_w1+7  ,box_l2-35,0.1])  cube([5, 5,pcb_h-0.1]);
        translate(v=[box_w2-13 ,box_l2-35,0.1])  cube([5, 5,pcb_h-0.1]);

        translate(v=[box_w1+12 ,box_l2-16,0.1])  cube([1.5 ,5,pcb_h-0.1]);
        translate(v=[box_w2-9  ,box_l2-16,0.1])  cube([1.5 ,5,pcb_h-0.1]);
    }
}

// width,depth,height,boxthickness,ledgethickness
module make_case(w,d,h,bt,lt) {
    dt=bt+lt;    // box+ledge thickness
    bt2=bt+bt;    // 2x box thickness
    // Now we just substract the shape we have created in the four corners
    color(CASEcolor) difference() {
        cube([w,d,h], center=false);
        if (rounded) {
            rounded_corner(-0.1,d+0.1, 0             ,-corner_radius,  corner_radius,-corner_radius);
            rounded_corner(w+0.1,d+0.1, -corner_radius,-corner_radius, -corner_radius,-corner_radius);
            rounded_corner(w+0.1,-0.1, -corner_radius,0             , -corner_radius, corner_radius);
            rounded_corner(-0.1,-0.1, 0             ,0             ,  corner_radius, corner_radius);
        }
        // empty inside, but keep a ledge for strength
        translate(v = [bt, bt, dt])   cube([w-bt2, d-bt2, h-(dt*2)], center = false);
        translate(v = [dt,dt,bt])     cube([w-(dt*2), d-(dt*2), h-bt2], center = false);
        // remove bottom and top deck
        translate(v = [box_thickness+2, box_thickness+5,-2]) {
            cube([inside_w-4, inside_l-10, box_h+4], center = false);
        }
    }
    if (!topframe) {
        make_deck(inside_w-4,inside_l-4,box_h-box_thickness, 12,3,5, holes=topholes, ledholes=ledholes, middle=topmiddle,screwholes=false,top=true);
    }
    if (!bottomframe) {
        make_deck(inside_w-4,inside_l-4,0, 12,3,5, holes=bottomholes,screwholes=bottomscrew,middle=false,top=false);
        if (bottomsupport) {
            make_supports();
        }
    }
}

module make_stud(x,y,z,w,h,l) {
    translate(v = [x, y, z]) cube([w, l, h], center = false);
}

module set_cutout(x,y,z,w,l,h) {
    color(CASEcolor)    translate(v = [x+(w/2), y+(l/2), z+(h/2)]) cube([w+0.4, l+0.2, h+0.2], center = true);
}

module set_cutoutv(x,y,z,w,l,h) {
    color(CASEcolor)    translate(v = [x+(w/2), y+(l/2), z+(h/2)]) cube([w+0.2, l+0.4, h+0.2], center = true);
}

module draw_pcbhold() {
  if (bottomclick) {
    color(CASEcolor) {
        translate(v=[0  ,22,2]) cube([box_thickness,4,pcb_c]);
        translate(v=[box_w1-0.1  ,22.5,pcb_c+0.1]) {
            difference() {
                cube([1, 3,2]);
                translate(v=[1,-0.1,0])  rotate(a=-30, v=[0,1,0])  cube([1.6, 3.2, 4]);
            }
        }
        translate(v=[0  ,60.5,2]) cube([box_thickness,5,pcb_c]);
        translate(v=[box_w1-0.1  ,61.5,pcb_c+0.1]) {
            difference() {
                cube([1,3,2]);
                translate(v=[1,-0.1,0])  rotate(a=-30, v=[0,1,0])  cube([1.6, 3.2, 4]);
            }
        }
        translate(v=[box_w2,29.5,2]) cube([box_thickness,4,pcb_c]);
        translate(v=[box_w2+0.1  ,30+3,pcb_c+0.1]) {
            rotate(a=180, v=[0,0,1]) difference() {
                cube([1, 3,3]);
                translate(v=[1,-0.1,0])  rotate(a=-30, v=[0,1,0])  cube([1.6, 3.2, 4]);
            }
        }
        translate(v=[box_w2,60.5,2]) cube([box_thickness,5,pcb_c]);
        translate(v=[box_w2+0.1  ,61+3.5,pcb_c+0.1]) {
            rotate(a=180, v=[0,0,1]) difference() {
                cube([1,3,3]);
                translate(v=[1,-0.1,0])  rotate(a=-30, v=[0,1,0])  cube([1.6, 3.2, 4]);
            }
        }
    }
  }
}

module split_top() {
    split1=box_w1+Cpwr_x;
    split2=split1+Cpwr_w;
    split3=box_w1+Csd_x - 12;   // min 16.5+28
    split4=box_w2 - 7;
    // Different splitlevels for the shells
    // 1st half on split level
    translate(v = [-1,  -1, casesplit-0.2])    cube([box_w+2, 21, 0.4], center = false);
    // back on 3 different levels
    translate(v = [-1,  20, casesplit-0.2])    cube([split1+1     , box_l, 0.4], center = false);
    translate(v = [split2, 20, pcb_c-0.2])     cube([split3-split2, box_l, 0.4], center = false);
    translate(v = [split3, 20, pcb_h-0.2])     cube([split4-split3, box_l, 0.4], center = false);
    translate(v = [split4, 20, casesplit-0.2]) cube([20           , box_l, 0.4], center = false);
}

module remove_top() {
    split1=box_w1+Cpwr_x;
    split2=split1+Cpwr_w;
    split3=box_w2 - 12;
    possd1=box_w1 + Csd_x - 0.3;
    widesd1=Csd_w+0.6;
    // Different splitlevels for the shells
    // 1st half on split level
    translate(v = [-1,  -1, casesplit])    cube([100,100, box_h], center = false);
    // back on 3 different levels
    translate(v = [split1, 20, pcb_c])     cube([split3-split1, box_l, box_h], center = false);
    translate(v = [possd1, 60, pcb_h-0.1])  cube([widesd1, box_l, 2], center = false);
//    translate(v = [split1, 20, pcb_c])     cube([20, box_l, box_h], center = false);
//    translate(v = [split2, 20, pcb_h])     cube([split3-split2, box_l, box_h], center = false);
  if (bottompcb) {
    translate(v = [-1,  -1, pcb_c])    cube([100,100, box_h], center = false);
  }
}

module remove_bottom() {
    split1=box_w1+Cpwr_x;
    split2=split1+Cpwr_w;
    split3=box_w2 - 12.1;
    possd1=box_w1 + Csd_x - 0.2;
    widesd1=Csd_w+0.6;
    // Different splitlevels for the shells
    // 1st half on split level
    translate(v = [-1,  -1, -1])    cube([box_w+2, box_l-6, casesplit+1], center = false);
    // back on 3 different levels
    translate(v = [-1, 20, -1])     cube([box_w+2  , box_l, pcb_c+1.1], center = false);
    translate(v = [-1, 20, -1])     cube([split1+1.1 , box_l, casesplit+1], center = false);
    translate(v = [-1, 20, -1])     cube([split2+1.1 , box_l, pcb_c+Cpwr_h+1.1], center = false);
    translate(v = [split3, 20, -1]) cube([20       , box_l, casesplit+1], center = false);
}

module draw_case(bottom, top) {
    difference() {
        union() {
            // make empty case
            difference() {
                make_case(box_w,box_l,box_h, box_thickness,stud_w, rounded=true);
                if (top != 0 && bottom == 0)    remove_bottom();
                if (top == 0 && bottom != 0)    remove_top();
            }
            color(CASEcolor) {
                if (bottom != 0 ) {
                    // add bottom studs for pcb
                    // add bottom studs for pcb
                    make_stud(box_w1       , box_l1         , 0, 4,pcb_h,4);      // rj45
                    make_stud(box_w1       , box_lc-stud_l/2, 0, stud_w,pcb_h,stud_l);      // hdmi
                    make_stud(box_w1, box_lc/2, 0, 4,pcb_h,stud_l);
                    make_stud(box_w1, box_lc+(box_lc/2)-5, 0, 4,pcb_h,stud_l);

                    make_stud(box_w1, box_l2-stud_l-8, 0, stud_w,pcb_h,stud_l);        // BEFORE pwr
                    make_stud(box_w2-stud_w, box_l1         , 0, stud_w,pcb_h,stud_l);      // leds
                    make_stud(box_w2-4, box_lc-stud_l/2, 0, 4,pcb_h,stud_l);                // RCA
                    make_stud(box_w2-stud_w, box_l2-stud_l  , 0, stud_w,pcb_h,stud_l);      // GPIO


                    translate(v=[box_w1+Cusb_x-6,box_l1,1])  cube([3.0, 4,pcb_h-1.1]);
                    translate(v=[box_w2-15.8    ,box_l1,1])  cube([3.0, 4,pcb_h-1.1]);

                    draw_pcbhold();
                }

                if (top != 0) {
                    // --- screw connection plates
                    translate(v = [box_w1 + Crj45_x+Crj45_w, box_l1, casesplit - 5.4]) {
                        cube([10, 3, box_h-(casesplit-5.4)], center = false);
                    }
                    translate(v = [box_w2-15, box_l2 - 1.5, casesplit - 5.4]) {
                            cube([8, 1.5, box_h-(casesplit-5.4)], center = false);
                    }
                    // extra support for shell
                    translate(v = [box_w1, box_l1, pcb_c+0.4]) {
                        cube([stud_w, 8, box_h-pcb_c-1], center = false);
                    }
                    translate(v = [box_w1, box_l2-10, pcb_c+0.4]) {
     	                   cube([stud_w, 10, box_h-pcb_c-1], center = false) ;
					 }
                    translate(v = [box_w1, box_l1+Chdmi_y+Chdmi_d+1.5, pcb_c+0.4]) {
                        cube([stud_w, 4, box_h-pcb_c-1], center = false);
                    }
                    translate(v = [box_w2-stud_w, box_l1, pcb_c+0.4]) {
                        cube([stud_w,10, box_h-pcb_c-1], center = false);
                    }
                    translate(v = [box_w2-stud_w, box_l1+Crca_y+Crca_d+1, pcb_c+0.4]) {
                        cube([stud_w, 4, box_h-pcb_c-1], center = false);
                    }
                }
            } // color
        } // end union
        // conn plate hole
        color(CASEcolor) {
        translate(v = [box_w1-5, box_l2-5, casesplit-3]) {
				rotate([0,90,0]) cylinder(r=0.5, h=10, $fn=100);
		 }
        translate(v = [box_w2-5, box_l1+5, casesplit-3]) {
				rotate([0,90,0]) cylinder(r=0.5, h=10, $fn=100);
		 }
        if (GPIOHOLE == 1 && bottom != 0) {
		     translate(v = [box_w2-5, box_l1+51, casesplit-GPIOsize]) cube([10,33.2,GPIOsize+0.1]);             
        }
        if (GPIOHOLE == 2 && top != 0) {
		     translate(v = [box_w2-5, box_l1+51, casesplit-0.1]) cube([10,33.2,GPIOsize]);             
        }
        }
        if (bottom != 0) {
            if (top == 0) {
                remove_top();
            } else {
                split_top();
            }
        }
        make_connholes();
    }
    if (bottom) {
        draw_pcbhold();
        if (DRAWpcb == 1)  make_pcb(alpha=0.5);
    }
} // end module
