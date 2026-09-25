"""Build the actual offset Pi spacer and four-ribbon guide STEP/STL parts.

Optional authoring dependency: cadquery-ocp 8.0.1.0.0 (OCP), Python 3.12.
No board mutations. STEP uses board XY with +Z up; the KiCad display copy is constructed
separately with Y reversed. Thread bores are tap-drill geometry.
See hw/mechanical/t1-ribbon-guide/README.md for machining/assembly dimensions.
"""
from pathlib import Path
import json,hashlib
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax2
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut,BRepAlgoAPI_Common
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
from OCP.StlAPI import StlAPI_Writer
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE,TopAbs_SOLID
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from assembly_fit import SPACER_BOXES,GUIDE_BOX,GUIDE_SLOTS,PI_TOP
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hw/mechanical/t1-ribbon-guide'

def box(v,display=False):
 x,y,z,X,Y,Z=v
 if display:y,Y=-Y,-y
 return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),X-x,Y-y,Z-z).Shape()
def cylinder(x,y,z,r,h,d=(0,0,1),display=False):
 if display:y=-y;d=(d[0],-d[1],d[2])
 return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*d)),r,h).Shape()
def fuse(a,b):return BRepAlgoAPI_Fuse(a,b).Shape()
def cut(a,b):return BRepAlgoAPI_Cut(a,b).Shape()
def parts(display=False):
 spacer=None
 for name,v in SPACER_BOXES.items():
  a=cylinder(61.5,52.5,v[2],3,v[5]-v[2],display=display) if name.endswith('boss') else box(v,display)
  spacer=a if spacer is None else fuse(spacer,a)
 # Top: 2.5 mm full thread engagement, 3.5 mm blind tap drill. Bottom: 5 mm.
 spacer=cut(spacer,cylinder(61.5,52.5,-1.6,1.025,3.5,(0,0,-1),display))
 spacer=cut(spacer,cylinder(61.5,52.5,PI_TOP,1.025,5,(0,0,1),display))
 for x in (33,37):spacer=cut(spacer,cylinder(x,56,-8.7,.8,4,(0,-1,0),display))
 guide=box(GUIDE_BOX,display)
 for x0,y0,z0,x1,y1,z1 in GUIDE_SLOTS:
  radius=(z1-z0)/2;zc=(z0+z1)/2
  slot=box((x0+radius,y0,z0,x1-radius,y1,z1),display)
  for x in (x0+radius,x1-radius):slot=fuse(slot,cylinder(x,y0,zc,radius,y1-y0,(0,1,0),display))
  guide=cut(guide,slot)
 # Round both entrance faces (including slot edges) so ribbons see no knife edge.
 fillet=BRepFilletAPI_MakeFillet(guide);edges=TopExp_Explorer(guide,TopAbs_EDGE)
 while edges.More():
  edge=TopoDS.Edge(edges.Current());c=BRepAdaptor_Curve(edge)
  a=c.Value(c.FirstParameter());b=c.Value(c.LastParameter())
  if abs(a.Y()-b.Y())<1e-7 and any(abs(abs(a.Y())-y)<1e-7 for y in (56,58)):fillet.Add(.15,edge)
  edges.Next()
 fillet.Build();assert fillet.IsDone(),'Guide edge radius failed';guide=fillet.Shape()
 for x in (33,37):guide=cut(guide,cylinder(x,55,-8.7,1.1,4,(0,1,0),display))
 assert BRepCheck_Analyzer(spacer).IsValid() and BRepCheck_Analyzer(guide).IsValid()
 return {'offset-spacer':spacer,'ribbon-guide':guide}

def main():
 OUT.mkdir(parents=True,exist_ok=True);hashes={};checks={}
 for display in (False,True):
  for name,shape in parts(display).items():
   exp=TopExp_Explorer(shape,TopAbs_SOLID);count=0
   while exp.More():count+=1;exp.Next()
   assert count==1,(name,'disconnected solids',count)
   if not display and name=='offset-spacer':
    for z in (-7.2,-10.2):
     passage=box((41.25,49,z-.665,72.75,56,z+.665))
     overlap=BRepAlgoAPI_Common(shape,passage).Shape();props=GProp_GProps();BRepGProp.VolumeProperties_s(overlap,props)
     assert props.Mass()<1e-8,(name,z,'cable interference')
     checks[str(z)]=dict(cable_window_overlap_mm3=props.Mass(),solid_count=count)
   folder=ROOT/'hw/models' if display else OUT
   stem=('T1_'+name if display else name)
   path=folder/(stem+'.step');w=STEPControl_Writer();w.Transfer(shape,STEPControl_AsIs);assert w.Write(str(path))==IFSelect_RetDone
   hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
   if not display:
    BRepMesh_IncrementalMesh(shape,.03,False,.15,True).Perform();w=StlAPI_Writer();w.ASCIIMode=False;assert w.Write(shape,str(folder/(stem+'.stl')))
 (OUT/'cad-provenance.json').write_text(json.dumps(dict(generator='hw/tools/ribbon_mechanics.py',units='mm',body_validation='OCP BRepCheck_Analyzer passed; one solid per part',window_checks=checks,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),ROOT/'hw/tools/assembly_fit.py')},sha256=hashes),indent=2)+'\n')
if __name__=='__main__':main()


