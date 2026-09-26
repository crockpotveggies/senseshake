"""Independently parse exported Gerber/Excellon and compare drills to KiCad.

Dependencies: pcbnew 9, gerbonara 1.5.0, cairosvg 2.8.2. Read-only on CAD.
"""
import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import pcbnew as p
from gerbonara import GerberFile, ExcellonFile, LayerStack
from gerbonara.utils import MM
import cairosvg
from jlcpcb_package import BOARD, ROOT, EXTENSIONS, write_json, validate_plot_inventory, check_drills, sha


def drill_key(x, y, diameter):
    return tuple(float(v) for v in (x, y, diameter))


def inspect(out):
    plots = out / 'gerbers'; review = out / 'review'
    manifest = json.loads((out / 'manifest.json').read_text())
    for source, expected_hash in manifest['source_sha256'].items():
        if sha(ROOT / source) != expected_hash:
            raise ValueError(f'Source changed since export: {source}')
    validate_plot_inventory(plots)
    b = p.LoadBoard(str(BOARD))
    expected = {'PTH': Counter(), 'NPTH': Counter(), 'front-in1': Counter(), 'in6-back': Counter()}
    for f in b.GetFootprints():
        for pad in f.Pads():
            dx, dy = p.ToMM(pad.GetDrillSize())
            if not dx: continue
            if abs(dx - dy) > 1e-6: raise ValueError('Slot added: extend independent drill comparison')
            x, y = p.ToMM(pad.GetPosition())
            kind = 'NPTH' if pad.GetAttribute() == p.PAD_ATTRIB_NPTH else 'PTH'
            expected[kind][drill_key(x, -y, dx)] += 1
    for via in b.GetTracks():
        if not isinstance(via, p.PCB_VIA): continue
        kind = 'PTH'
        if via.GetViaType() == p.VIATYPE_MICROVIA:
            kind = 'front-in1' if via.TopLayer() == p.F_Cu else 'in6-back'
        x, y = p.ToMM(via.GetPosition())
        expected[kind][drill_key(x, -y, p.ToMM(via.GetDrillValue()))] += 1
    result = {'parser': 'gerbonara 1.5.0', 'drill_coordinate_tolerance_mm': 0.001, 'drills': {}, 'layers': {}}
    for kind, want in expected.items():
        drill = ExcellonFile.open(plots / f'shakesense-trenz-hat-{kind}.drl')
        got = Counter(drill_key(o.x, o.y, o.tool.diameter) for o in drill.objects)
        check_drills(list(want.elements()), list(got.elements()))
        result['drills'][kind] = sum(got.values())
    for path in sorted(plots.iterdir()):
        if path.suffix[1:] not in EXTENSIONS: continue
        layer = GerberFile.open(path)
        if not layer.objects: raise ValueError(f'Empty plot: {path.name}')
        result['layers'][path.name] = {'objects': len(layer.objects), 'bounds_mm': layer.bounding_box(unit=MM)}
    stack = LayerStack.open(plots)
    for side in ('top', 'bottom'):
        # Plain SVG avoids filter effects unsupported by CairoSVG. Include
        # copper, legend and outline, but not opaque mask/paste overlays.
        svg = str(stack.to_svg(side_re=f'{side}|mechanical', margin=1,
                               force_bounds=((50, -106), (135, -50)),
                               colors={f'{side} copper': '#417e87', f'{side} silk': '#111111',
                                       'mechanical outline': '#222222', 'drill pth': '#ffffff',
                                       'drill npth': '#ffffff', 'drill unknown': '#ffffff'}))
        if side == 'bottom':
            root = ET.fromstring(svg)
            group = ET.Element('{http://www.w3.org/2000/svg}g', {'transform': 'translate(185 0) scale(-1 1)'})
            for child in list(root): root.remove(child); group.append(child)
            root.append(group); svg = ET.tostring(root, encoding='unicode')
        (review / f'gerber-{side}.svg').write_text(svg, encoding='utf-8')
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(review / f'gerber-{side}.png'), output_width=1600)
    write_json(review / 'independent-check.json', result)
    print(json.dumps({'drills': result['drills'], 'parsed_layers': len(result['layers'])}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    inspect(parser.parse_args().package)
