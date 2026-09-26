"""Read-only KiCad 9 export for a DAQHAT-01 JLCPCB engineering-review package.

Run with a Python that can import pcbnew (the portable lab or WSL). Never
rewrites the routed board, fills zones, substitutes components, or releases an
order. PDF generation and independent Gerber inspection are separate steps.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD_DIR = ROOT / 'hw/boards/groundlark-daqhat-01'
BOARD = BOARD_DIR / 'groundlark-daqhat-01.kicad_pcb'
LAYERS = ['F.Cu', *[f'In{i}.Cu' for i in range(1, 7)], 'B.Cu',
          'F.Paste', 'B.Paste', 'F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'Edge.Cuts']
EXTENSIONS = {'gtl', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'gbl',
              'gtp', 'gbp', 'gto', 'gbo', 'gts', 'gbs', 'gm1'}
CATALOG = {
    'LSM6DSOTR': ('C2655100', 'https://jlcpcb.com/partdetail/LSM6DSOTR/C2655100'),
    'TCA9534PWR': ('C783615', 'https://jlcpcb.com/partdetail/TexasInstruments-TCA9534PWR/C783615'),
}
PLACEHOLDERS = {'JP1', 'J4'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def natural(ref):
    return re.sub(r'\d+', lambda m: m[0].zfill(6), ref)


def physical(ref):
    return not re.fullmatch(r'(H|TP)\d+', ref)


def check_reference_sets(bom, placements):
    a = [r for row in bom for r in row['Designator'].split(',')]
    b = [row['Designator'] for row in placements]
    if len(set(a)) != len(a) or len(set(b)) != len(b):
        raise ValueError('Duplicate assembly designator')
    if set(a) != set(b):
        raise ValueError(f'BOM/CPL mismatch: {sorted(set(a) ^ set(b))}')


def check_drills(expected, actual, tolerance=0.001001):
    """Match each hit once, allowing KiCad's 1 um Excellon quantization."""
    remaining = list(actual)
    for x, y, diameter in expected:
        match = next((i for i, (ax, ay, ad) in enumerate(remaining)
                      if abs(x-ax) <= tolerance and abs(y-ay) <= tolerance
                      and abs(diameter-ad) < 1e-6), None)
        if match is None:
            raise ValueError(f'Missing drill: {(x, y, diameter)}')
        remaining.pop(match)
    if remaining:
        raise ValueError(f'Unexpected drills: {remaining}')


def validate_plot_inventory(folder):
    present = {p.suffix[1:] for p in folder.iterdir() if p.is_file()}
    if not EXTENSIONS <= present:
        raise ValueError(f'Missing manufacturing layers: {sorted(EXTENSIONS - present)}')
    drills = list(folder.glob('*.drl'))
    if len(drills) != 4:
        raise ValueError('Expected separate PTH, NPTH, L1-L2 and L7-L8 drill files')
    spans = []
    for path in drills:
        text = path.read_text()
        if 'METRIC' not in text:
            raise ValueError('Drill units must be millimetres')
        line = next((s for s in text.splitlines() if 'TF.FileFunction' in s), '')
        spans.append(line)
    expected = ['NonPlated,1,8,NPTH', 'Plated,1,8,PTH', 'Plated,1,2,Blind', 'Plated,7,8,Blind']
    for value in expected:
        if not any(value in line for line in spans):
            raise ValueError(f'Missing drill layer attribution: {value}; got {spans}')


def run(*args):
    result = subprocess.run([str(a) for a in args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def export(out, quantity):
    import pcbnew as p
    if quantity < 1:
        raise ValueError('Assembly quantity must be positive')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output must be new or empty; preserve earlier packages')
    out.mkdir(parents=True, exist_ok=True)
    source_paths = [BOARD, BOARD.with_suffix('.kicad_pro'), BOARD_DIR / 'bom.csv',
                    BOARD_DIR / 'verification.json']
    before = {str(f.relative_to(ROOT)): sha(f) for f in source_paths}
    validated = json.loads((BOARD_DIR / 'verification.json').read_text())['input_sha256']
    for source in (BOARD, BOARD.with_suffix('.kicad_pro'), BOARD_DIR / 'bom.csv'):
        key = str(source.relative_to(ROOT))
        if validated.get(key) != sha(source):
            raise ValueError(f'Source differs from recorded validation: {key}')
    b = p.LoadBoard(str(BOARD))
    refs = {f.GetReference(): f for f in b.GetFootprints()}
    with (BOARD_DIR / 'bom.csv').open(newline='', encoding='utf-8') as stream:
        source = list(csv.DictReader(stream))
    if len(source) != len(refs) or {r['Reference'] for r in source} != set(refs):
        raise ValueError('Source BOM does not match PCB footprints')
    if any(r['DNP'] != 'False' for r in source):
        raise ValueError('New DNP variant requires explicit assembly review')
    plots = out / 'gerbers'; plots.mkdir()
    evidence = out / 'review'; evidence.mkdir()
    run('kicad-cli', 'pcb', 'drc', BOARD, '--format', 'json', '--severity-all',
        '--exit-code-violations', '-o', evidence / 'drc.json')
    drc = json.loads((evidence / 'drc.json').read_text())
    for key in ('violations', 'unconnected_items', 'schematic_parity'):
        if drc.get(key):
            raise ValueError(f'Native DRC failed: {key}')
    run('kicad-cli', 'pcb', 'export', 'gerbers', BOARD, '-o', str(plots) + '/',
        '-l', ','.join(LAYERS), '--subtract-soldermask', '--precision', '6')
    run('kicad-cli', 'pcb', 'export', 'drill', BOARD, '-o', str(plots) + '/',
        '--format', 'excellon', '--drill-origin', 'absolute', '--excellon-units', 'mm',
        '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'alternate',
        '--excellon-separate-th', '--generate-report', '--report-path', evidence / 'drill-report.txt')
    validate_plot_inventory(plots)
    for side, layers in [('top', 'F.Fab,F.SilkS,Edge.Cuts'), ('bottom', 'B.Fab,B.SilkS,Edge.Cuts')]:
        extra = ['--mirror'] if side == 'bottom' else []
        run('kicad-cli', 'pcb', 'export', 'svg', BOARD, '-o', evidence / f'cad-fab-{side}.svg',
            '-l', layers, '--mode-single', '--fit-page-to-board', '--exclude-drawing-sheet',
            '--sketch-pads-on-fab-layers', '--black-and-white', *extra)
    placements, review = [], []
    groups = defaultdict(list)
    geometry = []
    for row in sorted(source, key=lambda r: natural(r['Reference'])):
        ref = row['Reference']; f = refs[ref]
        pads = [pad for pad in f.Pads() if pad.GetNumber()]
        if not physical(ref):
            continue
        if not pads:
            raise ValueError(f'Physical component without numbered pads: {ref}')
        tht = any(pad.GetAttribute() == p.PAD_ATTRIB_PTH for pad in pads)
        side = 'Bottom' if f.IsFlipped() or ref == 'J1' else 'Top'
        # Standard SMD footprints are body-centred. Pin-1-anchored THT packages
        # need a body-centre estimate; use the pad pattern for review only.
        x, y = p.ToMM(f.GetPosition())
        method = 'KiCad SMD body origin; confirm against feeder definition'
        if tht:
            xs, ys = zip(*(p.ToMM(pad.GetPosition()) for pad in pads))
            x, y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            method = 'THT pad-pattern centre; manual assembly drawing controls'
        placement = dict(Designator=ref, MidX=f'{x:.6f}mm', MidY=f'{-y:.6f}mm',
                         Layer=side, Rotation=f'{f.GetOrientationDegrees() % 360:.6f}')
        placements.append(placement)
        mpn = row['MPN'].removeprefix('Samtec ')
        groups[(mpn, row['Value'], row['Footprint'])].append(ref)
        code, url = CATALOG.get(mpn, ('', ''))
        hold = 'Unverified catalog match / supply allocation'
        if code: hold = 'Exact catalog match; stock and process still unconfirmed'
        if ref in PLACEHOLDERS: hold = 'BLOCK: source uses descriptive placeholder instead of orderable MPN'
        if ref == 'Q1': hold = 'BLOCK: 2N7002 manufacturer / full ordering code unspecified'
        review.append(dict(Designator=ref, MPN=mpn, Process='THT' if tht else 'SMT',
                           Side=side, Position_basis=method, Rotation_status='REVIEW REQUIRED',
                           Sourcing_status=hold, Catalog_URL=url))
        pin1 = next((pad for pad in pads if pad.GetNumber() == '1'), None)
        geometry.append(dict(reference=ref, side=side, process='THT' if tht else 'SMT',
                             x_mm=x, y_mm=y, rotation_deg=f.GetOrientationDegrees() % 360,
                             pin1_mm=list(p.ToMM(pin1.GetPosition())) if pin1 else None,
                             pads=[dict(number=a.GetNumber(), xy_mm=list(p.ToMM(a.GetPosition())),
                                        size_mm=list(p.ToMM(a.GetSize()))) for a in pads]))
    bom, procurement = [], []
    for (mpn, value, footprint), designators in sorted(groups.items()):
        designators.sort(key=natural); code, url = CATALOG.get(mpn, ('', ''))
        bom.append({'Comment': value, 'Designator': ','.join(designators),
                    'Footprint': footprint, 'MPN': mpn, 'LCSC Part #': code})
        procurement.append({'MPN': mpn, 'Designator': ','.join(designators),
                            'Per_HAT': len(designators), 'Requested_HATs': quantity,
                            'Installed_total': quantity * len(designators),
                            'Purchase_quantity': 'TBD: supplier MOQ and assembly attrition',
                            'LCSC Part #': code, 'Catalog_URL': url})
    check_reference_sets(bom, placements)
    write_csv(out / 'BOM-review.csv', list(bom[0]), bom)
    write_csv(out / 'CPL-review.csv', list(placements[0]), placements)
    write_csv(evidence / 'assembly-review.csv', list(review[0]), review)
    write_csv(out / 'procurement.csv', list(procurement[0]), procurement)
    # Conservative full via-fill callout: every through-via is resin filled and
    # copper capped, every laser microvia copper filled and planarized. This
    # avoids omissions where a via barrel only partly overlaps a solder pad.
    vias = []
    for track in b.GetTracks():
        if not isinstance(track, p.PCB_VIA): continue
        x, y = p.ToMM(track.GetPosition())
        micro = track.GetViaType() == p.VIATYPE_MICROVIA
        vias.append(dict(X_mm=x, Y_mm=-y, Type='laser blind' if micro else 'through',
                         From=b.GetLayerName(track.TopLayer()), To=b.GetLayerName(track.BottomLayer()),
                         Drill_mm=p.ToMM(track.GetDrillValue()), Pad_mm=p.ToMM(track.GetWidth(track.TopLayer())),
                         Fill='copper filled / planarized' if micro else 'resin filled / copper capped'))
    vias.sort(key=lambda v: (v['X_mm'], v['Y_mm']))
    write_csv(out / 'via-processing.csv', list(vias[0]), vias)
    write_json(evidence / 'placement-geometry.json', geometry)
    if before != {str(f.relative_to(ROOT)): sha(f) for f in source_paths}:
        raise ValueError('Source changed during export')
    with zipfile.ZipFile(out / 'DAQHAT-01-Gerbers-REVIEW.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(plots.iterdir()):
            if path.suffix[1:] in EXTENSIONS | {'drl', 'gbrjob'}:
                archive.write(path, path.name)
    manifest = {
        'status': 'ENGINEERING REVIEW ONLY - NOT RELEASED FOR MANUFACTURE',
        'requested_assembled_HATs': quantity,
        'published_standard_PCBA_minimum': 2,
        'source_commit': run('git', '-C', ROOT, 'rev-parse', 'HEAD'),
        'kicad': run('kicad-cli', 'version'), 'source_sha256': before,
        'board_mm': [85, 56], 'nominal_thickness_mm': 1.6,
        'copper_layers': LAYERS[:8], 'copper_thickness_mm': [0.035] * 8,
        'dielectric_thickness_mm': [0.08, 0.1, 0.18, 0.58, 0.18, 0.1, 0.08],
        'mask_thickness_mm': 0.01, 'stack_status': 'PROVISIONAL; supplier must approve or propose a reviewed alternative',
        'counts': {'physical_placements': len(placements), 'BOM_lines': len(bom),
                   'excluded_holes_testpads': len(source) - len(placements),
                   'vias': dict(Counter(v['Type'] for v in vias)),
                   'assembly': dict(Counter(f"{r['Side']} {r['Process']}" for r in review))},
        'coordinate_convention': 'Absolute KiCad origin; X right, Y up; mm. CPL/Excellon/Gerber same origin. Bottom NOT mirrored.',
        'release_holds': [
            'Quantity one needs a written exception or user agreement to the published two-piece minimum.',
            'Approve exact eight-layer 1+6+1 HDI stack, via fill/capping and copper weights.',
            'JLC Standard assembly frame/rails and fiducials; 85x56 board is below 70mm minimum dimension.',
            'Resolve JP1/J4 ordering codes, Q1 manufacturer, and exact procurement allocation for ALL parts.',
            'Verify every rotation and centroid against JLC component definitions; J1 is bottom-mounted THT.',
            'Approve mixed SMT/THT assembly, reflow constraints and sensor handling; do not substitute parts.',
            'Review panelized Gerbers, drill spans, polarity/pin 1 and assembly preview before payment.',
        ],
    }
    write_json(out / 'manifest.json', manifest)
    print(json.dumps(manifest['counts'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--quantity', type=int, default=1)
    args = parser.parse_args()
    export(args.output.resolve(), args.quantity)
