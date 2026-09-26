# DAQHAT-01 supplier placement correction

The former CPL exported raw KiCad angles. Those angles are relative to KiCad's
footprint zero, which differs from several selected supplier connector and IC definitions.
The circuit/PCB positions were correct; the assembly upload orientation was not.

Use **both** `BOM-review.csv` and `CPL-review.csv` from the local ignored folder
`hw/releases/groundlark-daqhat-01-jlcpcb-placement-20260926-c91-c92/`.
Keep `DAQHAT-01-Gerbers-REVIEW.zip` from
`groundlark-daqhat-01-jlcpcb-review-20260926-one-hat`. No Gerber update is needed.
The new BOM selects Megastar ZX-PM2.54-2-20PY / C7499354 for J1, replacing the
unmatchable Samtec selection. It retains all shortage replacements and 117 placements / 38 lines
for one HAT. Earlier packages remain intact.

| Reference | Original angle | Supplier CPL angle |
| --- | ---: | ---: |
| J1 (Bottom, C7499354) | 90° | 0° |
| J4 | 0° | 270° |
| JP1, JP80, JP81 | 90° | 0° |
| J80, J81 | 0° | 180° |
| J82 | 90° | 270° |
| J83 | 270° | 270° |
| J90 | 180° | 180° |
| U1, U22, U41, U42 | 0° | 270° |
| U100, U101, U102, U103 (Bottom) | 0° | 270° |
| Q1, U40, U51, U52 | 0° | 180° |
| D90 (Bottom) | 90° | 0° |

The full BOM audit adds 13 IC/transistor/protection-device corrections to the
eight connector corrections. No external ribbon connectors have been
reintroduced. J4/JP1/JP80/JP81 are straight pin headers.

## Programmatic basis

`hw/assembly/daqhat-01-jlcpcb-placement.json` freezes the public EasyEDA/LCSC
catalog footprint PAD records, origin, UUID, retrieval date and response hash
for the exact selected MPN and C-number. Source URLs are included per entry.
The parser follows the [KiCad EasyEDA format documentation](https://dev-docs.kicad.org/en/import-formats/easyeda/index.html):
10 mil units become millimetres, and Y is inverted into CPL coordinates.

For connectors, `jlcpcb_placement.py` fits a rigid rotation/translation using
numbered pins. All individual pads must fit
within 0.01 mm. The ten connectors check 321 physical pads; maximum observed
error is below 0.0002 mm. Tiny origin shifts below 0.000003 mm reflect catalog
rounding. Both grounded mounting pads of every LSHM connector are included,
even though the native footprint gives them a common pad number.

For SMT, `jlcpcb_smd_placement.py` tries quarter turns at the unchanged native
body centre. It checks every numbered pad's rectangular envelope overlap:
at least 60% of the smaller pad in each axis. All present SMT fits exceed 88%.
Different libraries use different land lengths, so fitting centroids exactly
would incorrectly shift some asymmetric three- and five-pin packages.
This is an orientation/registration check, not solder-joint qualification.
Polarized packages must have one unique passing angle. Nonpolar two-terminal
resistors, MLCCs and the fuse retain the native angle when 0/180 equivalents
both fit; no unnecessary half-turns are introduced.

Bottom SMT reflects local catalog X, then rotates CCW into the top-view board
frame. Only local pad geometry is reflected; absolute CPL XY stays unchanged.
Unmirrored fitting fails the numbered-pad checks on underside ICs such as U102.
U40's catalog pad 4 is mapped to its second native pad 2: the
[TI TLV1117LV datasheet](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf)
identifies the tab and pin 2 as OUT. Both physical output lands are checked.

Changing an MPN, C-number, native footprint, pin count, pitch or mounting
geometry invalidates the mapping. Bottom parts require an explicit projection
entry tied to the selected part; top mappings cannot silently be used on Bottom.
J1's C7499354 entry fits its 40-hole catalog grid in the common board projection,
changing 90° to 0° while keeping Bottom and XY = (82.510000, -53.499999) mm.
This fixes the long-axis mismatch; it does not validate the private supplier
bottom-side model or its pin-1 marker. The socket is an unkeyed straight 2x20 part.
All 117 placements must have a mapping or a part-bound explicit exception;
an unaudited new reference fails export. The full exporter and correction overlay use the same solver;
re-running it does not add a second rotation correction.

## Validation and remaining review

The hardware suite includes placement regressions covering all
quadrants, translation, pin polarity, mirrored/scaled patterns, missing/duplicate
contacts, displaced mounting pads, identity changes and repeated exports.
See the [regression coverage matrix](assembly-regressions.md) for inventory,
invalid-geometry and complete export/overlay tests added after this correction.
A fresh full exporter run passes native DRC and is compared against the overlay.
No native board or source BOM was changed by this correction.

The audit covers all 38 BOM lines and **117 placements / 703 physical pads**
with catalog registrations and no missing-footprint exceptions. C91/C92 now
select [KEMET C0603C102J5GAC7867 / C140950](https://jlcpcb.com/partdetail/KEMET-C0603C102J5GAC7867/C140950).
[KEMET's specification](https://search.kemet.com/component-documentation/download/specsheet/C0603C102J5GACTU)
lists this ordering code as an alias of the original C0603C102J5GACTU:
1 nF, 50 V, C0G, ±5%, 0603. The original C2181873 catalog footprint was unavailable;
the replacement has an exact public footprint and passes both numbered-pad checks.
JLCPCB showed 616 available to order, minimum one, at USD 0.0212 each on
26 September 2026. Stock is not reserved. Both capacitors remain at 0 degrees on
Top; the CPL is byte-identical to the preceding `full-bom` correction.
`placement-audit.csv` records all 117 rows, with detailed pin counts and fit
metrics in `placement-audit.json`. These are catalog checks, not private-model approval.

Public catalog geometry is not approval of JLCPCB's private feeder/model data.
After replacing the CPL, remove previous manual rotation adjustments and review
pin 1 in the order preview. The other components still need that preview check.
J1 now selects the bottom-mounted [Megastar ZX-PM2.54-2-20PY / C7499354](https://jlcpcb.com/partdetail/ZX-PM2.54-2-20PY/C7499354),
listed in JLCPCB's assembly catalog. Its 8.5 mm body is shorter than the original
Samtec socket: revised riser/spacers and bottom-side orientation still require
review. The native CAD/3D stack remains the original Samtec baseline; that fit
evidence does not qualify this replacement. J1 CPL is now corrected to 0°;
replace the CPL rather than uploading only the corrected BOM. Check the bottom
preview once after clearing previous manual rotation overrides.
Tests bind the MPN, manufacturer and C-number in both BOM and procurement output,
and require a documented substitution. No stock reservation or order was made.

Reproduce in WSL/Linux with KiCad's Python module:

```sh
python3 -m unittest discover -s hw/tests -v
python3 hw/tools/jlcpcb_placement_overlay.py \
  --base hw/releases/groundlark-daqhat-01-jlcpcb-review-20260926-one-hat \
  --output hw/releases/NEW-placement-review
```

The overlay tool requires a new output directory, verifies the base checksums
and validated design inputs, and preserves existing manufacturing holds.
