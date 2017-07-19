# Use openscad binary from path unless specified in environment variable
OPENSCAD?=openscad

all: top.dxf bottom.dxf side1.dxf side2.dxf end1.dxf end2.dxf mask.dxf tank_support.dxf rpi_support.dxf rear_support.dxf

clean:
	rm *.dxf

top.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_TOP=true box_structure.scad

bottom.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_BOTTOM=true box_structure.scad

side1.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_SIDE1=true box_structure.scad

side2.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_SIDE2=true box_structure.scad

end1.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_END1=true box_structure.scad

end2.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_END2=true box_structure.scad

mask.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_MASK=true box_structure.scad

tank_support.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_TANK_SUPPORT=true box_structure.scad

rpi_support.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_RPI_SUPPORT=true box_structure.scad

rear_support.dxf: box_structure.scad
	"$(OPENSCAD)" -o $@ -D DXF_REAR_SUPPORT=true box_structure.scad
