"""Create a new audited CPL/current-BOM overlay without altering Gerbers."""
import argparse
import json
from pathlib import Path
import shutil
from jlcpcb_bom import REGISTRY, build_bom
from jlcpcb_bom_overlay import export_overlay, read_csv, bundle_overlay
from jlcpcb_package import BOARD, BOARD_DIR, ROOT, sha, write_csv, write_json, check_reference_sets
from jlcpcb_placement import MAPPINGS, board_geometry, correct_placements


def exception_summary(audit):
    missing=[a['reference'] for a in audit if 'pads_checked' not in a]
    if not missing:
        return 'No supplier-footprint exceptions remain; all placements have catalog mappings.'
    return f'Unverified supplier-footprint exceptions: {", ".join(missing)}. Check these in the order preview.'


def export_placement_overlay(base, out):
    import pcbnew as p
    # Solve before writing any output; export_overlay checks all design hashes.
    bom, _, selections = build_bom(read_csv(BOARD_DIR/'bom.csv'), 1)
    before = read_csv(base/'CPL-review.csv')
    cpl, audit = correct_placements(before, board_geometry(p.LoadBoard(str(BOARD))), selections)
    check_reference_sets(bom,cpl)
    report = export_overlay(base,out)
    write_csv(out/'CPL-review.csv',list(cpl[0]),cpl)
    write_json(out/'placement-audit.json',audit)
    audit_rows=[dict(Designator=a['reference'],MPN=selections[a['reference']]['mpn'],
        **{'JLCPCB Part #':selections[a['reference']]['lcsc']},
        Status=a['status'],Method=a.get('fit_method','unverified'),
        Before_deg=next(r['Rotation'] for r in before if r['Designator']==a['reference']),
        After_deg=next(r['Rotation'] for r in cpl if r['Designator']==a['reference']),
        Pads_checked=a.get('pads_checked',0),Minimum_pad_envelope_overlap=a.get('min_pad_overlap_fraction',''),
        Note=a.get('reason','Supplier order preview remains required')) for a in audit]
    write_csv(out/'placement-audit.csv',list(audit_rows[0]),audit_rows)
    shutil.copyfile(MAPPINGS,out/'supplier-placement-mappings.json')
    report.pop('unchanged_CPL_sha256')
    report.update(status='CATALOG PLACEMENT CORRECTION; ORDER PREVIEW REVIEW REQUIRED',
                  original_CPL_sha256=sha(base/'CPL-review.csv'),
                  corrected_CPL_sha256=sha(out/'CPL-review.csv'),
                  placement_changes=[dict(reference=a['reference'],before=a['before'],after=a['after'])
                                     for a in audit if 'before' in a and a['before']!=a['after']],
                  catalog_fitted_components=sum('pads_checked' in a for a in audit))
    report['unverified_placements']=[a for a in audit if 'pads_checked' not in a]
    report['pads_checked']=sum(a.get('pads_checked',0) for a in audit)
    for path in [MAPPINGS,Path(__file__),ROOT/'hw/tools/jlcpcb_placement.py',ROOT/'hw/tools/jlcpcb_smd_placement.py',ROOT/'hw/tools/jlcpcb_package.py',ROOT/'hw/tools/jlcpcb_bom_overlay.py']:
        report['source_sha256'][path.relative_to(ROOT).as_posix()]=sha(path)
    report['placement_limitations']=[
        'Public EasyEDA/LCSC catalog geometry is not confirmation of JLC private assembly-model zero orientation.',
        'Mapped connectors fit catalog pads in the board coordinate projection. Unmapped rotations remain unverified.',
        'SMT orientation checks pin identities and pad-envelope overlap at unchanged native body centres. Bottom SMT mirrors local X then rotates CCW; absolute board XY is not mirrored.',
        exception_summary(audit),
        f'J1 is bottom-mounted {selections["J1"]["mpn"]} / {selections["J1"]["lcsc"]}; corrected catalog-axis rotation still needs supplier bottom-model/pin-1 preview and stack-height review.']
    write_json(out/'validation.json',report)
    changes='\n'.join(f'| {a["reference"]} | {float(a["before"]["Rotation"]):g} | {float(a["after"]["Rotation"]):g} |'
                      for a in audit if 'before' in a and a['before']['Rotation']!=a['after']['Rotation'])
    (out/'README.md').write_text(f'''# DAQHAT-01 placement correction

Use BOTH BOM-review.csv and CPL-review.csv in this folder. This replaces the
shortages BOM overlay and all earlier CPL files. Keep the Gerber ZIP from
{base.name}; PCB, copper, drills and component positions are unchanged.
Do not upload this overlay ZIP as Gerbers.

One HAT: {len(bom)} BOM rows and {len(cpl)} installed parts, including prior shortage replacements.

| Reference | Previous CPL degrees | Corrected CPL degrees |
| --- | ---: | ---: |
{changes}

All {len(cpl)} placements were audited: {report['catalog_fitted_components']} have
catalog-based mappings checking {report['pads_checked']} physical pads.
{exception_summary(audit)}
See placement-audit.csv / placement-audit.json for every component.
C91/C92 select {selections['C91']['mpn']} / {selections['C91']['lcsc']}:
{selections['C91']['sourcing_note']}
The additional IC corrections include U100/U101/U102 and U103 on Bottom.
SMT body centres stay fixed; land-pattern envelope overlap permits legitimate
differences in pad lengths. This is not solder-joint or private feeder qualification.

J1 now selects {selections['J1']['manufacturer']} {selections['J1']['mpn']} /
{selections['J1']['lcsc']} in the BOM. {selections['J1']['sourcing_note']}
J1 CPL now uses the catalog-derived 0 degree orientation instead of the old
90 degrees. It remains Bottom at the same absolute XY coordinates. Check the
supplier's bottom-side model/pin-1 marker in the preview; its 8.5mm socket also
still needs stack-height review. These changes do not close the physical fit holds.

After replacing the CPL, check the order preview against pin 1. Remove any
earlier manual rotation adjustments so they are not applied twice. Public
catalog geometry does not prove the private JLC assembly model uses that zero.
All existing sourcing/process/physical qualification holds remain open.
''',encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=export_placement_overlay(args.base.resolve(),args.output.resolve())
    bundle_overlay(args.output.resolve(),name='DAQHAT-01-PLACEMENT-CORRECTION.zip')
    print(json.dumps({k:report[k] for k in ['physical_placements','BOM_lines','catalog_fitted_components','placement_changes']},indent=2))
