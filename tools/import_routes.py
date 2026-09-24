"""Import this project's restricted Freerouting SES format, then fill GND planes.

KiCad's SES importer is not exposed by the CLI. This small importer accepts only the
through-via/straight-track format used here, checks placement, and fails closed
on unknown route objects. Run check_design.py afterwards: import is not signoff.
"""
from pathlib import Path
import sys,re,json
import pcbnew as p
import sexpdata as sx

ROOT=Path(__file__).resolve().parents[1]
REMOVED_HAT_REFS={'U30','C30','C31','R30','R31','R32','R33','R34','R35','J3','F1','C50','D1','D2','TP3'}
REMOVED_HAT_NETS={'REMOTE_3V3','D_SCL_N','D_SCL_P','D_SDA_N','D_SDA_P'}
def children(n,key): return [x for x in n if isinstance(x,list) and x and str(x[0])==key]
def child(n,key): return next(iter(children(n,key)))
def vec(x,y): return p.VECTOR2I(round(x),round(y))

def main(name):
    folder=ROOT/'hardware'/name; path=folder/(name+'.kicad_pcb')
    b=p.LoadBoard(str(path)); s=sx.load(open(folder/(name+'.ses')))
    routes=child(s,'routes'); res=child(routes,'resolution')
    assert str(res[1])=='um'; factor=1000/float(res[2])
    fps={f.GetReference():f for f in b.GetFootprints()}
    for c in children(child(s,'placement'),'component'):
        for pl in children(c,'place'):
            if name=='shakesense-hat' and str(pl[1]) in REMOVED_HAT_REFS:continue
            fp=fps[str(pl[1])]; xy=fp.GetPosition()
            assert abs(xy.x-float(pl[2])*factor)<101 and abs(xy.y+float(pl[3])*factor)<101, pl
            assert str(pl[4])=='front'
    layers={'F.Cu':p.F_Cu,'B.Cu':p.B_Cu}
    if b.GetCopperLayerCount()==6:layers.update({'In2.Cu':p.In2_Cu,'In3.Cu':p.In3_Cu})
    nets=b.GetNetsByName()
    for track in list(b.GetTracks()):
        if not track.IsLocked(): b.Delete(track)
    # Re-running replaces pours but preserves design-rule keepouts.
    for i in range(b.GetAreaCount()-1,-1,-1):
        zone=b.GetArea(i)
        if not zone.GetIsRuleArea(): b.Delete(zone)
    for net in children(child(routes,'network_out'),'net'):
        if name=='shakesense-hat' and str(net[1]) in REMOVED_HAT_NETS:continue
        ni=nets[str(net[1])]
        for obj in net[2:]:
            typ=str(obj[0])
            if typ=='wire':
                pathdata=child(obj,'path');layer=layers[str(pathdata[1])]
                width=round(float(pathdata[2])*factor);coords=pathdata[3:]
                points=[vec(float(coords[i])*factor,-float(coords[i+1])*factor) for i in range(0,len(coords),2)]
                for start,end in zip(points,points[1:]):
                    if start==end: continue
                    t=p.PCB_TRACK(b);t.SetStart(start);t.SetEnd(end);t.SetWidth(width);t.SetLayer(layer);t.SetNet(ni);b.Add(t)
            elif typ=='via':
                m=re.fullmatch(r'Via\[0-'+str(b.GetCopperLayerCount()-1)+r'\]_(\d+):(\d+)_um',str(obj[1]));assert m,obj
                v=p.PCB_VIA(b);v.SetPosition(vec(float(obj[2])*factor,-float(obj[3])*factor));v.SetWidth(int(m[1])*1000);v.SetDrill(int(m[2])*1000);v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(ni);b.Add(v)
            else: raise ValueError(obj)
    size=json.loads((folder/'electrical.json').read_text())['size_mm']
    for layer in (p.In1_Cu,p.In4_Cu if b.GetCopperLayerCount()==6 else p.In2_Cu):
        z=p.ZONE(b);z.SetLayer(layer);z.SetNet(nets['GND']);z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.Outline().NewOutline()
        for x,y in [(50.4,50.4),(49.6+size[0],50.4),(49.6+size[0],49.6+size[1]),(50.4,49.6+size[1])]: z.Outline().Append(vec(p.FromMM(x),p.FromMM(y)))
        b.Add(z)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
    print(name,len(b.GetTracks()),'tracks/vias; inner GND planes filled')

if __name__=='__main__':
    for name in sys.argv[1:] or ['shakesense-hat','shakesense-field-head']: main(name)
