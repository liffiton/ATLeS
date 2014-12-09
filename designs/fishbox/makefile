
all: top.dxf bottom.dxf side1.dxf side2.dxf end1.dxf end2.dxf light_bar.dxf

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

light_bar.dxf: fishbox.scad
	"$(OPENSCAD)" -o $@ -D DXF_LIGHT_BAR=true fishbox.scad

