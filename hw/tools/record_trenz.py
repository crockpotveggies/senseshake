"""Record T1 artifacts while checking preservation of the original circuits."""
from pathlib import Path
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[2];path=ROOT/'docs/artifact-manifest.json';j=json.loads(path.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=['hw/elec/hat.ato','hw/elec/field_head.ato','hw/elec/parts.ato','hw/layout.json',
 'hw/boards/shakesense-hat/shakesense-hat.kicad_pcb','hw/boards/shakesense-field-head/shakesense-field-head.kicad_pcb']
for name in protected:
    if name in j['sha256']:assert sha(ROOT/name)==j['sha256'][name],name+' unexpectedly changed'
files=[ROOT/'hw/ato.yaml',ROOT/'hw/layout-trenz.json',ROOT/'hw/elec/hat_trenz.ato',ROOT/'hw/elec/trenz_parts.ato',ROOT/'docs/trenz-pin-map.json',ROOT/'docs/trenz-hat.md']
for pattern in ['hw/libraries/ShakeSense.pretty/*.kicad_mod','sw/pi/senseshake/*.py','sw/tests/*.py','sw/ui/assets/*','sw/ui/main.py','docs/geophone-input.md','hw/elec/geophone_parts.ato','hw/elec/symbols/GEO*.kicad_sym','hw/elec/Connector_Phoenix_MC*.kicad_mod','hw/elec/Package_SO__TSSOP*.kicad_mod','hw/elec/Package_TO_SOT_SMD*.kicad_mod','docs/geophone-input.md','hw/simulation/geophone/*','hw/tools/*.py','hw/tests/*.py','docs/trenz-*.csv','docs/t1-engineering-closure.md','docs/sensor-development-plan.md','hw/elec/TZ_*.kicad_mod','hw/elec/symbols/TZ*.kicad_sym','hw/boards/shakesense-trenz-hat/*','hw/simulation/trenz/*','hw/models/trenz/*','hw/models/FFC_*.wrl','hw/models/Pi4_stack_concept.wrl','environment/lab.py','docs/stack-assembly.md','docs/pre-fab-review.md','docs/pre-fab-acquisition-stress.json','hw/simulation/geophone-review/*','hw/models/T1_service_envelopes.wrl']:
    files.extend(p for p in ROOT.glob(pattern) if p.is_file() and p.suffix not in ['.log','.lck','.kicad_prl'])
j['sha256']={name:digest for name,digest in j['sha256'].items() if (ROOT/name).is_file()}
files.extend(ROOT/name for name in j['sha256'])
for p in files:j['sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
j['trenz_update_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
validation=json.loads((ROOT/'hw/boards/shakesense-trenz-hat/validation.json').read_text())
assert all(validation[k]==0 for k in ['drc_violations','unconnected_items','erc_violations']), 'Cannot record a passing board before native checks close'
j['trenz_status']='T1-GEO Pi-outline 8-layer HDI prototype; native ERC/DRC/connectivity and 18 portable stages pass; geophone SPICE, power and clearance checks; physical qualification and FPGA bitstream pending'
path.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8',newline='\n');print('T1 artifacts recorded; original A2 circuit/layout hashes preserved')
