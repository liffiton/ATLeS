# Use openscad binary from path unless specified in environment variable
OPENSCAD?=openscad

all: top.dxf bottom.dxf side1.dxf side2.dxf end1.dxf end2.dxf mask.dxf tank_support.dxf camera_support.dxf rpi_support.dxf

clean:
	rm *.dxf

top.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_TOP=true fishbox.scad

bottom.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_BOTTOM=true fishbox.scad

side1.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_SIDE1=true fishbox.scad

side2.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_SIDE2=true fishbox.scad

end1.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_END1=true fishbox.scad

end2.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_END2=true fishbox.scad

mask.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_MASK=true fishbox.scad

tank_support.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_TANK_SUPPORT=true fishbox.scad

camera_support.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_CAMERA_SUPPORT=true fishbox.scad

rpi_support.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_RPI_SUPPORT=true fishbox.scad

