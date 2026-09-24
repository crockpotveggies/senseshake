"""Place atopile's compiled KiCad footprints; never reconstruct electrical nets.

layout.json contains mechanical placement/BOM presentation only. Connectivity
is read exclusively from the compiled .ato board. Derived schematics are for
review; electrical changes must be made in elec/*.ato and rebuilt.
"""
from pathlib import Path
import json,csv,re,types,shutil,sys,sexpdata as sx
import pcbnew as p
from kicad_support import add_shape,add_text,schematic,uid,v
from restore_keepouts import restore
from fixed_routes import add as add_fixed_fanout
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware'

def main():
    layoutfile='layout-trenz.json' if '--trenz' in sys.argv else 'layout.json'
    for name,spec in json.loads((ROOT/layoutfile).read_text()).items():
        if len(sys.argv)>1 and '--trenz' not in sys.argv and name not in sys.argv[1:]:continue
        target=spec.get('target','hat' if name.endswith('-hat') else 'field_head')
        ishat=target in ('hat','trenz_hat')
        folder=HW/name;folder.mkdir(exist_ok=True)
        b=p.LoadBoard(str(ROOT/'layout'/target/(target+'.kicad_pcb')))
        assert b.GetFootprints(),'Run ato build first'
        layers=6 if ishat else 4
        b.SetCopperLayerCount(layers)
        ds=b.GetDesignSettings();ds.m_CopperEdgeClearance=p.FromMM(.3);ds.m_MinClearance=p.FromMM(.15);ds.m_TrackMinWidth=p.FromMM(.15);ds.m_ViasMinSize=p.FromMM(.6);ds.m_MinThroughDrill=p.FromMM(.3)
        for obj in list(b.GetTracks()):b.Delete(obj)
        for obj in list(b.GetDrawings()):b.Delete(obj)
        for i in range(b.GetAreaCount()-1,-1,-1):b.Delete(b.GetArea(i))
        fps={f.GetReference():f for f in b.GetFootprints()}
        parts=[]
        for meta in spec['parts']:
            meta=dict(meta);typ=meta.pop('type');ref=meta['ref']
            if ref not in fps:
                assert not typ,('Missing compiled component',ref)
                fp=p.FootprintLoad(str(ROOT/'elec'),meta['local_fp']);fp.SetReference(ref);b.Add(fp)
            else:fp=fps[ref]
            if target=='field_head' and ref=='J1':
                # Restore the complete manufacturer footprint geometry after
                # compiler conversion, retaining each compiled physical pin net.
                old=fp;pin_nets={pad.GetNumber():pad.GetNet() for pad in old.Pads() if pad.GetNumber()}
                fp=p.FootprintLoad(str(ROOT/'elec'),meta['local_fp'])
                assert {pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}==set(pin_nets)
                fp.SetReference(ref);b.Add(fp)
                for pad in fp.Pads():
                    if pad.GetNumber():pad.SetNet(pin_nets[pad.GetNumber()])
                b.Delete(old)
            fp.SetPosition(v(50+meta['xy'][0],50+meta['xy'][1]));fp.SetOrientationDegrees(meta['angle'])
            fp.SetValue(meta['value']);fp.SetDNP(meta['dnp'])
            fp.Reference().SetVisible(True);fp.Reference().SetTextSize(v(.8,.8));fp.Reference().SetTextThickness(p.FromMM(.12));fp.Reference().SetPosition(v(50+meta['xy'][0],46.5+meta['xy'][1]));fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
            fp.Reference().SetLayer(p.F_Fab)
            fp.Value().SetVisible(False)
            # Set native schematic linkage for the derived review schematic.
            fp.SetPath(p.KIID_PATH('/'+uid(name)+'/'+uid(name+'/'+meta['section'])+'/'+uid(name+'/'+ref)))
            fp.SetFPID(p.LIB_ID('ShakeSense',meta['local_fp']))
            pads={pad.GetNumber():pad.GetNetname() or None for pad in fp.Pads() if pad.GetNumber()}
            # Atopile creates unique singleton nets for intentionally open pins.
            meta['pins']=pads
            parts.append(types.SimpleNamespace(**meta))
        w,h=spec['size']
        for a,c in [((0,0),(w,0)),((w,0),(w,h)),((w,h),(0,h)),((0,h),(0,0))]:add_shape(b,50+a[0],50+a[1],50+c[0],50+c[1],p.Edge_Cuts,.05)
        for layer in (p.In1_Cu,p.In4_Cu if layers==6 else p.In2_Cu):
            z=p.ZONE(b);z.SetLayer(layer);z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(False);z.SetDoNotAllowCopperPour(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);z.Outline().NewOutline()
            for x,y in [(50,50),(50+w,50),(50+w,50+h),(50,50+h)]:z.Outline().Append(v(x,y))
            b.Add(z)
        if ishat:
            z=p.ZONE(b);z.SetLayer(p.F_Cu);z.SetIsRuleArea(True);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);z.Outline().NewOutline()
            tiltbox=[(92.2,73.7),(97.8,73.7),(97.8,82.3),(92.2,82.3)] if target=='trenz_hat' else [(88.2,74.7),(93.8,74.7),(93.8,83.3),(88.2,83.3)]
            for x,y in tiltbox:z.Outline().Append(v(x,y))
            b.Add(z)
            # Short RF connection uses retained reviewed coordinates; impedance
            # remains subject to the selected fabrication stackup.
            nets=b.GetNetsByName()
            pts=[(68.75,97.3),(69.8,97.3),(71.95,95.15),(71.95,94)] if target=='hat' else [(68.75,99.3),(71.8,99.3),(73.95,97.15),(73.95,96)]
            for a,c in zip(pts,pts[1:]):
                t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*c));t.SetWidth(p.FromMM(.3));t.SetLayer(p.F_Cu);t.SetNet(nets['GNSS_RF']);t.SetLocked(True);b.Add(t)
            if target=='hat':
                add_text(b,'ShakeSense A2 | atopile',87,104.5,.85)
                add_text(b,'COLDFOOT / RUN-1',145,53,.8)
                add_text(b,'XYZ MOTION',70,61,.8)
                add_text(b,'NO GEOPHONE',83,87,.8)
            # Raised module envelope on assembly layer. Components beneath must
            # clear the 3mm mating stack; no tall parts under this rectangle.
            outline=[(30,8),(80,8),(80,48),(30,48)] if target=='trenz_hat' else [(90,19),(104,19),(104,35),(90,35)]
            for a,c in zip(outline,outline[1:]+outline[:1]):add_shape(b,50+a[0],50+a[1],50+c[0],50+c[1],p.Dwgs_User,.12)
            if target=='trenz_hat':
                add_text(b,'ShakeSense T1 / 200T',84,104.8,.8)
                add_text(b,'3V3 ONLY',57,57,.8)
                add_text(b,'JTAG',132,67,.8)
        else:
            add_text(b,'ShakeSense FIELD A2',97,91,.8);add_text(b,'RM3100 / XYZ',68,54,.8)
        title=p.TITLE_BLOCK();title.SetTitle(name+' / atopile prototype');title.SetRevision('T1' if target=='trenz_hat' else 'A2');title.SetDate('2026-09-23');b.SetTitleBlock(title)
        restore(b)
        if target=='hat':add_fixed_fanout(b)
        # Stock models are resolved by KiCad 9. Portable custom models are added
        # by tools/models.py after routing, without changing connectivity.
        path=folder/(name+'.kicad_pcb');p.SaveBoard(str(path),b)
        lib=HW/'libraries'/'ShakeSense.pretty';lib.mkdir(exist_ok=True)
        for fpfile in (ROOT/'elec').glob('*.kicad_mod'):shutil.copyfile(fpfile,lib/fpfile.name)
        derived={'size':spec['size'],'parts':parts};schematic(name,derived,folder)
        for sch in folder.glob('*.kicad_sch'):
            s=sch.read_text().replace('A0 DRAFT','A2 PROTOTYPE').replace('Engineering draft - module interface and fabrication release on hold.','Atopile-derived circuit review schematic - prototype, not released.')
            sch.write_text(s)
        (folder/'electrical.json').write_text(json.dumps({'source':'atopile compiled PCB; do not edit','size_mm':spec['size'],'copper_layers':layers,'parts':[vars(x) for x in parts]},indent=2))
        with open(folder/'bom.csv','w',newline='') as f:
            writer=csv.writer(f);writer.writerow(['Reference','Value','MPN','Footprint','DNP','Note'])
            for x in parts:writer.writerow([x.ref,x.value,x.mpn,x.local_fp,x.dnp,x.note])
        (folder/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "ShakeSense") (type "KiCad") (uri "${KIPRJMOD}/../libraries/ShakeSense.pretty") (options "") (descr "Atopile atomic parts")))')
        project={'meta':{'filename':name+'.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.3}}},'net_settings':{'classes':[{'name':'Default','clearance':.15,'track_width':.15,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.2,'diff_pair_via_gap':.25}],'meta':{'version':3}}}
        (folder/(name+'.kicad_pro')).write_text(json.dumps(project,indent=2))
        p.ExportSpecctraDSN(b,str(folder/(name+'.dsn')))
        data=(folder/(name+'.dsn')).read_text()
        for layer in ('In1.Cu','In4.Cu' if layers==6 else 'In2.Cu'):
            data=data.replace(f'(layer {layer}\n      (type signal)',f'(layer {layer}\n      (type power)')
            data=re.sub(r'    \(wire_keepout "" \(polygon '+re.escape(layer)+r'[^)]*\)\)\n','',data)
        data=data.replace('(width 200)','(width 150)').replace('(clearance 200.1','(clearance 150.1')
        data=data.replace('(clearance 200)', '(clearance 150)')
        # Specctra treats brackets as part of bare names; sexpdata treats them
        # as list delimiters. Preserve these tokens losslessly while editing.
        tree=sx.loads(data.replace('(string_quote ")','(string_quote quote)').replace('[','__LB__').replace(']','__RB__'))
        network=next(x for x in tree if isinstance(x,list) and str(x[0])=='network')
        default=next(x for x in network if isinstance(x,list) and str(x[0])=='class')
        power=[x for x in default[2:] if not isinstance(x,list) and str(x) in {'PI_5V','PI_3V3','SENS_3V3','USB_VBUS','USB_5V','V3_SENSOR','V3','CF_REG_3V3','CF_3V3','CF_SW'}]
        default[:]=[x for x in default if isinstance(x,list) or x not in power]
        # Fine escapes route first; widen_power.py subsequently retains wider
        # power copper wherever actual KiCad DRC allows it.
        network.append([sx.Symbol('class'),'Power',*power,[sx.Symbol('circuit'),[sx.Symbol('use_via'),f'Via[0-{layers-1}]_600:300_um']],[sx.Symbol('rule'),[sx.Symbol('width'),150],[sx.Symbol('clearance'),150]]])
        (folder/(name+'.dsn')).write_text(sx.dumps(tree).replace('(string_quote quote)','(string_quote ")').replace('__LB__','[').replace('__RB__',']'))
        print(name,len(parts),'placed compiled parts')

if __name__=='__main__':main()
