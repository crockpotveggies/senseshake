"""Independent Trenz carrier pin/geometry checks plus KiCad DRC/ERC.

Critical module pin fixture is transcribed from vendor revision-03 schematic
page 6 and mechanical drawing, independently of the atopile authoring script.
"""
from pathlib import Path
from collections import Counter
import json,subprocess,xml.etree.ElementTree as ET
import pcbnew as p
from gpio_audit import check as check_gpio
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'hw/boards/shakesense-trenz-hat';N=F.name
board=p.LoadBoard(str(F/(N+'.kicad_pcb')));compiled=p.LoadBoard(str(ROOT/'hw/layout/trenz_hat/trenz_hat.kicad_pcb'))
def pins(b):
    result={}
    for f in b.GetFootprints():
        for q in f.Pads():
            if not q.GetNumber():continue
            key=(f.GetReference(),q.GetNumber());net=q.GetNetname()
            assert key not in result or result[key]==net,('Inconsistent repeated pad number',key)
            result[key]=net
    return result
bp,cp=pins(board),pins(compiled);assert all(bp.get(k)==n for k,n in cp.items()),'Compiled circuit changed during layout'
fixture={
 'J80':{1:'FPGA_VIN',3:'FPGA_VIN',5:'FPGA_VIN',13:'FPGA_VIN',15:'FPGA_VIN',9:'FPGA_3V3',11:'FPGA_3V3',14:'FPGA_3V3',28:'FPGA_EN1',89:'FPGA_JTAGEN'},
 'J81':{2:'FPGA_VIN',4:'FPGA_VIN',6:'FPGA_VIN',8:'FPGA_VIN',1:'FPGA_3V3',3:'FPGA_3V3',7:'FPGA_3V3',9:'FPGA_3V3',10:'FPGA_3V3',12:'FPGA_3V3',91:'FPGA_3V3',11:'FPGA_UART_RX',13:'FPGA_UART_TX',14:'FPGA_RESET_N',18:'FPGA_CONFIG_RESET_N',93:'JTAG_TMS',95:'JTAG_TDI',97:'JTAG_TDO',99:'JTAG_TCK'}}
gpio_report=check_gpio(bp)
check_gpio(cp)
spec=json.loads((ROOT/'hw/layout-trenz.json').read_text())[N]
assert board.GetCopperLayerCount()==spec['copper_layers']==8
assert abs(p.ToMM(board.GetDesignSettings().GetBoardThickness())-1.6)<1e-6
planes={board.GetLayerName(z.GetLayer()) for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND'}
assert planes==set(spec['ground_layers'])=={'In2.Cu','In5.Cu'}
microvias=[t for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetViaType()==p.VIATYPE_MICROVIA]
assert microvias,'HDI routing missing'
for via in microvias:
    pair=[board.GetLayerName(via.TopLayer()),board.GetLayerName(via.BottomLayer())]
    assert pair in spec['hdi']['microvia_pairs'],pair
    assert abs(p.ToMM(via.GetWidth(via.TopLayer()))-.3)<1e-6 and abs(p.ToMM(via.GetDrillValue())-.1)<1e-6
from stackup import block_span
text=(F/(N+'.kicad_pcb')).read_text();a,z=block_span(text,'(stackup');stack=text[a:z]
assert stack.count('(type "copper")')==8 and stack.count('(thickness 0.08)')==2
checks=0
for ref,m in fixture.items():
    for modulepin,net in m.items():
        carrierpin=modulepin+1 if modulepin%2 else modulepin-1
        assert bp[(ref,str(carrierpin))]==net,(ref,modulepin,net);checks+=1
for pin,net in {1:'JTAG_TMS',2:'JTAG_TDI',3:'JTAG_TDO',4:'JTAG_TCK',5:'GND',6:'FPGA_3V3'}.items():assert bp[('J84',str(pin))]==net
for pin,net in {1:'PI_3V3',2:'PI_5V',4:'PI_5V',8:'PI_UART_TX',10:'PI_UART_RX',11:'FPGA_RESET_GPIO',22:'FPGA_IO_ENABLE'}.items():assert bp[('J1',str(pin))]==net
assert bp[('U51','3')]=='PI_3V3' and bp[('U51','7')]=='FPGA_3V3'
assert bp[('R62','1')]=='FPGA_IO_ENABLE' and bp[('R62','2')]=='GND'
assert bp[('J83','1')]=='EXT_3V3' and bp[('F80','2')]=='FPGA_VIN'
assert len({'PI_5V','PI_3V3','EXT_3V3','FPGA_VIN','FPGA_3V3'} & set(bp.values()))==5
# Shared sensor circuitry must preserve A2 pad connectivity exactly.
base=pins(p.LoadBoard(str(ROOT/'hw/boards/shakesense-hat/shakesense-hat.kicad_pcb')))
sensor_refs={'U11','U12','U13','U14','U20','U40','U41','U42','U43'}
degrees=Counter(base.values())
for k,n in base.items():
    if k[0] in sensor_refs and degrees[n]>1 and 'GNSS' not in n:assert bp[k]==n,(k,n,bp[k])
fps={f.GetReference():f for f in board.GetFootprints()}
pad_ids=[q.m_Uuid.AsString() for f in board.GetFootprints() for q in f.Pads()]
assert len(pad_ids)==len(set(pad_ids)),'Duplicate pad UUIDs corrupt KiCad report item references'
for ref,xy in {'J80':(55,44),'J81':(55,12),'J82':(34,28),'H80':(33,11),'H81':(77,11),'H82':(33,45),'H83':(77,45),'H1':(3.5,3.5),'H2':(61.5,3.5),'H3':(3.5,52.5),'H4':(61.5,52.5)}.items():
    q=fps[ref].GetPosition();assert abs(p.ToMM(q.x)-50-xy[0])<.001 and abs(p.ToMM(q.y)-50-xy[1])<.001,ref
for ref,xy,angle in [('J86',(17,22),0),('J87',(17,39),180),('J88',(57,20),0),('J89',(57,37),180)]:
    f=fps[ref];q=f.GetPosition()
    assert f.IsFlipped() and f.GetLayer()==p.B_Cu,(ref,'must be underside')
    assert abs(p.ToMM(q.x)-50-xy[0])<.001 and abs(p.ToMM(q.y)-50-xy[1])<.001,ref
    assert (f.GetOrientationDegrees()-angle)%360<.001,ref
    # Component courtyard must stay inside the outline; DRC checks pairwise overlap.
    box=f.GetBoundingBox(False,False)
    assert box.GetLeft()>p.FromMM(50) and box.GetRight()<p.FromMM(135),ref
    assert box.GetTop()>p.FromMM(50) and box.GetBottom()<p.FromMM(106),ref
edge=board.GetBoardEdgesBoundingBox();assert abs(p.ToMM(edge.GetWidth())-85)<.1 and abs(p.ToMM(edge.GetHeight())-56)<.1
for num,xy in {'1':(8.38,4.77),'2':(8.38,2.23),'39':(56.64,4.77),'40':(56.64,2.23)}.items():
    q=next(q for q in fps['J1'].Pads() if q.GetNumber()==num).GetPosition()
    assert abs(p.ToMM(q.x)-50-xy[0])<.001 and abs(p.ToMM(q.y)-50-xy[1])<.001
subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(F/'schematic-netlist.xml'),str(F/(N+'.kicad_sch'))],check=True,stdout=subprocess.DEVNULL)
tree=ET.parse(F/'schematic-netlist.xml');sp={}
for net in tree.findall('.//nets/net'):
    for node in net.findall('node'):sp[(node.get('ref'),node.get('pin'))]=net.get('name')
degree=Counter(bp.values())
for k,n in bp.items():
    if degree[n]>1:assert sp.get(k)==n,(k,n,sp.get(k))
for kind,extension,check in [('pcb','kicad_pcb','drc'),('sch','kicad_sch','erc')]:
    subprocess.run(['kicad-cli',kind,check,'--format','json','-o',str(F/(check+'.json')),str(F/(N+'.'+extension))],check=True,stdout=subprocess.DEVNULL)
drc=json.loads((F/'drc.json').read_text());erc=json.loads((F/'erc.json').read_text())
er=[v for s in erc['sheets'] for v in s['violations']]
report={'status':'T1 engineering prototype; not fabrication released','outline_mm':[85,56],**gpio_report,'compiled_pin_checks':len(cp),'critical_module_pin_checks':checks,'drc_violations':len(drc['violations']),'unconnected_items':len(drc['unconnected_items']),'erc_violations':len(er),'tracks_and_vias':len(board.GetTracks()),'copper_layers':8,'microvias':len(microvias),'hdi_structure':'1+6+1','limits':['Provisional HDI stack requires manufacturer DFM, filled/planarized via-in-pad and GNSS RF impedance review','No FPGA bitstream port or hardware test performed','External regulated 3.3 V supply required; confirm 3.201–3.399 V at module under startup/load','Copper resistance, heating, sensor thermal drift, EMI and physical mating remain unqualified','FFC cable routing, GPIO loading and high-speed signal integrity remain unqualified','Pi rendering is conceptual; Trenz rendering uses vendor generic revision-03 STEP']}
report['limits'] = [
 'Fabrication process approval is owned by the project owner; calculations use the recorded provisional stack',
 'Single Racotech geophone input; analog noise, cable coupling and ADC timing require physical qualification',
 'J83 source: 3.35 V +/-0.5%, total hot loop resistance <=30 milliohms, <=3 A; verify startup and load waveform at module',
 'Pi4 conceptual stack uses SSQ-120-02-G-D riser; selected cooler, cables and mating need physical fit verification',
 'No FPGA bitstream or physical sensor/rail/thermal/EMI/high-speed GPIO tests performed',
 'Pi FIFO/IRQ and geophone polling are tested on modeled buses; no GNSS or absolute UTC source on T1-GEO',
 'Trenz rendering uses vendor generic revision-03 STEP']
(F/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert not drc['violations'] and not drc['unconnected_items'] and not er
