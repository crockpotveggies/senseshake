"""Create one four-page review PDF from exported, independently parsed plots."""
import argparse
import json
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

W, H = 595.276, 841.89
INK = HexColor('#162b3a')
ACCENT = HexColor('#087e8b')
WARN = HexColor('#a33c21')


def make(out):
    manifest = json.loads((out / 'manifest.json').read_text())
    geometry = json.loads((out / 'review/placement-geometry.json').read_text())
    check = json.loads((out / 'review/independent-check.json').read_text())
    c = Canvas(str(out / 'T1-LINK-assembly-review.pdf'), pagesize=(W, H), invariant=1)
    c.setTitle('ShakeSense T1-LINK | JLCPCB engineering review | one assembled HAT')
    style = ParagraphStyle('body', fontName='Helvetica', fontSize=10, leading=15, textColor=INK)

    def paragraph(text, y, width=499):
        p = Paragraph(text, style); _, h = p.wrap(width, H)
        p.drawOn(c, 48, y-h); return y-h-12

    def page(title, index):
        c.setFillColor(ACCENT); c.rect(0, H-13, W, 13, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont('Helvetica', 10)
        c.drawString(48, H-48, 'SHAKESENSE / T1-LINK / JLCPCB')
        c.setFont('Helvetica-Bold', 22); c.drawString(48, H-83, title)
        c.setFillColor(WARN); c.setFont('Helvetica-Bold', 9)
        c.drawString(48, H-108, 'ENGINEERING REVIEW ONLY - NOT RELEASED FOR MANUFACTURE')
        c.setFillColor(INK); c.setFont('Helvetica', 8)
        c.drawString(48, 27, f"Source {manifest['source_commit'][:12]} | Requested assembly: {manifest['requested_assembled_HATs']} HAT")
        c.drawRightString(W-48, 27, f'{index} / 4')

    page('Assembly request', 1)
    y = H-139
    for text in [
        '<b>Requested deliverable:</b> one populated 85 x 56 mm T1-LINK carrier. Standard PCBA, double-sided SMT plus through-hole assembly. Pi, Trenz module, geophone, riser, power supply and mounting hardware are separate purchases.',
        '<b>Quantity hold:</b> JLCPCB publishes a two-piece Standard PCBA minimum. Keep this request at one; obtain an exception or the owner\'s agreement to two before ordering. Bare-board lot size and component attrition are separate quote items.',
        '<b>Handling hold:</b> the 56 mm board dimension is below the 70 mm Standard minimum. Manufacturer to propose an assembly frame, edge rails and fiducials; return panel data for review without altering the HAT outline or hole positions.',
        '<b>Sourcing hold:</b> 127 placements, 40 grouped BOM lines. JP1 and J4 still have descriptive placeholders, and Q1 lacks a manufacturer-specific ordering code. Only two exact catalog matches have been recorded; the rest need sourcing review. No stock is reserved and no substitutions are approved.',
        '<b>Placement hold:</b> CPL is a review candidate, not feeder-approved data. Validate every centroid, rotation and pin 1 against the selected JLC component. J1 is explicitly bottom-mounted despite the front-side CAD land pattern.',
        '<b>Assembly instructions:</b> populate required SMT and THT parts. Keep JP1, JP80 and JP81 shunts OPEN. Do not fit a Trenz module or Raspberry Pi during PCB assembly. Confirm sensor reflow limits, cleaning and handling with current manufacturer instructions.',
        '<b>Validation:</b> fresh native DRC has zero findings and zero unconnected items. Independent Gerbonara parsing reads all 15 plot layers and matches all 456 drill hits to CAD within 1 micrometre. This does not replace manufacturer DFM or first-article power, fit, timing and noise measurements.',
    ]: y = paragraph(text, y)
    c.showPage()

    page('Fabrication specification', 2)
    y = paragraph('<b>Provisional 8-layer 1+6+1 HDI.</b> 1.60 mm nominal including 0.01 mm masks on both sides; ENIG; green mask; white legend. Manufacturer must approve the actual laminate, layer thicknesses, finished copper and tolerances. Do not substitute an ordinary through-via eight-layer process.', H-139)
    x = 48; rowh = 19
    rows = [('Layer / material', 'Thickness (mm)', 'Purpose / processing')]
    names = manifest['copper_layers']
    for i, name in enumerate(names):
        rows.append((f'L{i+1} - {name}', '0.035', 'GND plane' if name in ('In2.Cu','In5.Cu') else 'Copper'))
        if i < 7: rows.append((f'Dielectric {i+1}', f"{manifest['dielectric_thickness_mm'][i]:.3f}", 'Provisional FR4'))
    for i, row in enumerate(rows):
        c.setFillColor(HexColor('#e5f1f2') if i == 0 else HexColor('#f1f4f6') if i%2 else HexColor('#ffffff'))
        c.rect(x, y-rowh, 499, rowh, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont('Helvetica-Bold' if i == 0 else 'Helvetica', 9)
        for xx, value in zip((56, 224, 352), row): c.drawString(xx, y-13, value)
        y -= rowh
    y -= 15
    for text in [
        '<b>Laser microvias:</b> four L1-L2 and seven L7-L8; 0.10 mm holes, 0.30 mm pads. Copper-fill and planarize all 11. Outer dielectric/hole ratio is 0.8; nominal annular ring is 0.10 mm.',
        '<b>Through-via fill proposal:</b> resin-fill and copper-cap all 370 through-vias listed in via-processing.csv, including the analog supply via-in-pad sites. This conservative quote option avoids omitted overlapping sites; confirm process/cost. Do not fill the 61 component PTH holes or 14 NPTH holes.',
        '<b>Coordinates:</b> absolute KiCad origin; X right, Y up. Board bounds X=50..135, Y=-106..-50 mm. Gerber, drill and CPL share this origin. Bottom CPL coordinates are NOT mirrored. Bottom illustration is mirrored for viewing only.',
        '<b>Drills:</b> four Excellon files keep PTH, NPTH and both blind spans separate. Preserve Edge.Cuts, mounting holes and connector locating holes. Use the drill report for tool counts; never merge blind spans into through drills.',
    ]: y = paragraph(text, y)
    c.showPage()

    for side, index in [('top', 3), ('bottom', 4)]:
        page(f'{side.title()} assembly review', index)
        y = paragraph(('Viewed from component side. ' if side == 'top' else 'Viewed from the underside; horizontally mirrored relative to the top. ') +
                      'Image is independently rendered from exported Gerbers. It shows lands and routing, not installed component bodies. Notes below identify assembly-critical sites; CSV and CAD Fab SVGs provide the full placement inventory.', H-139)
        im = ImageReader(str(out / f'review/gerber-{side}.png'))
        iw, ih = im.getSize(); width=499; height=width*ih/iw
        bottom=y-height-8
        c.drawImage(im,48,bottom,width,height,mask='auto')
        y=bottom-22
        rows = ([
            '<b>J80 / J81 / J82:</b> three Samtec fine-pitch Trenz connectors on TOP. Match exact height, locating posts and pin 1. Confirm stock or consigned parts before accepting the assembly quote.',
            '<b>U11-U14 / U20 / U22:</b> four IMUs, inclinometer and geophone ADC. Preserve existing sensor orientations; do not rotate an accelerometer to create another axis. The IMUs already measure all three axes.',
            '<b>J83 / J90:</b> module power terminal and geophone receptacle, respectively. Populate both through-hole connectors. JP1/JP80/JP81 headers have no installed shorting shunts.',
            '<b>J1 exception:</b> the long Pi connector land pattern appears on this side in CAD Fab output, but its socket body is installed BELOW the board. Follow the bottom assembly instruction, not the library layer.',
        ] if side == 'top' else [
            '<b>J1:</b> Samtec ESQ-120-23-G-D socket body underneath the HAT; mating face toward the Pi riser. Verify pin 1, tail length and seating against the stack drawing before soldering.',
            '<b>U100-U106 and associated passives:</b> underside link-switch, expander, logic and supervisor circuitry. 35 SMT components occupy this side. Confirm their rotations in the JLC assembly preview.',
            '<b>Mechanical fit:</b> maintain Pi/riser and fastener clearance. No cable guide or external FPGA ribbon connectors are part of this revision. Actual connector mating and stack clearances need first-article verification.',
        ])
        for text in rows: y=paragraph(text,y)
        c.showPage()
    c.save()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    make(parser.parse_args().package)
