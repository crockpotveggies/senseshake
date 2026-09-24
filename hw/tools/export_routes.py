"""Resume routing from the saved native PCB, retaining completed copper."""
from pathlib import Path
import sys,json
import pcbnew as p
from assemble_pcb import export_dsn
ROOT=Path(__file__).resolve().parents[2]
if __name__=='__main__':
    name=sys.argv[1];folder=ROOT/'hw/boards'/name
    board=p.LoadBoard(str(folder/(name+'.kicad_pcb')))
    # Pours are regenerated after routing; keep all authored rule areas.
    for zone in list(board.Zones()):
        if not zone.GetIsRuleArea():board.Delete(zone)
    layout='layout-trenz.json' if name=='shakesense-trenz-hat' else 'layout.json'
    spec=json.loads((ROOT/'hw'/layout).read_text())[name]
    export_dsn(board,folder/(name+'.dsn'),spec.get('signal_via_mm',[.6,.3]),spec.get('ground_layers'))
    print('Exported existing copper for continued routing:',name)
