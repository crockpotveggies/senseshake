"""Trim only KiCad-reported dangling copper, verifying connectivity after each pass."""
from pathlib import Path
import subprocess,json,sys
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
for name in sys.argv[1:] or ['shakesense-hat','shakesense-field-head']:
    folder=ROOT/'hardware'/name;path=folder/(name+'.kicad_pcb');out=folder/'drc.json'
    for iteration in range(80):
        subprocess.run(['kicad-cli','pcb','drc','--format','json','-o',str(out),str(path)],check=True,stdout=subprocess.DEVNULL)
        r=json.loads(out.read_text())
        remove={i['uuid'] for v in r['violations'] if v['type'] in {'track_dangling','via_dangling'} for i in v['items']}
        # Removal of a connector can leave isolated branches. Only allow an
        # initial airwire whose two ends are themselves reported dangling.
        assert all(all(i['description'].startswith(('Track [','Via [')) for i in v['items']) for v in r['unconnected_items']),r['unconnected_items']
        if not remove:break
        b=p.LoadBoard(str(path));count=0
        for t in list(b.GetTracks()):
            if t.m_Uuid.AsString() in remove and not t.IsLocked():b.Delete(t);count+=1
        if not count:break
        p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(path),b)
    print(name,'dangling trim passes',iteration)
    assert not r['unconnected_items'],r['unconnected_items']
