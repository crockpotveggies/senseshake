"""Record T1 artifacts while checking preservation of the original circuits."""
from pathlib import Path
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'docs/artifact-manifest.json';j=json.loads(path.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=['elec/hat.ato','elec/field_head.ato','elec/parts.ato','layout.json',
 'hardware/shakesense-hat/shakesense-hat.kicad_pcb','hardware/shakesense-field-head/shakesense-field-head.kicad_pcb']
for name in protected:
    if name in j['sha256']:assert sha(ROOT/name)==j['sha256'][name],name+' unexpectedly changed'
files=[ROOT/'ato.yaml',ROOT/'layout-trenz.json',ROOT/'elec/hat_trenz.ato',ROOT/'elec/trenz_parts.ato',ROOT/'docs/trenz-pin-map.json',ROOT/'docs/trenz-hat.md']
for pattern in ['tools/*.py','elec/TZ_*.kicad_mod','elec/symbols/TZ*.kicad_sym','hardware/shakesense-trenz-hat/*','simulation/trenz/*','hardware/models/trenz/*']:
    files.extend(p for p in ROOT.glob(pattern) if p.is_file() and p.suffix not in ['.log','.lck','.kicad_prl'])
for p in files:j['sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
j['trenz_update_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
j['trenz_status']='T1 Pi-outline engineering prototype; ERC/DRC/connectivity pass; hardware and FPGA bitstream qualification pending'
path.write_text(json.dumps(j,indent=2));print('T1 artifacts recorded; original A2 circuit/layout hashes preserved')
