# JLCPCB assembled DAQHAT-01 HAT

**Current package:** `groundlark-daqhat-01-jlcpcb-review-20260926-one-hat` uses three
IMUs, no dedicated inclinometer, and the corrected local bypass loops. Its BOM
uses exact ordering codes and verified catalog identities instead of value-only
matching. It supersedes the `imu-bypass` upload package, the older `standard6`
four-IMU/inclinometer package and all HDI exports.
Do not submit an older ZIP.

**Current assembly correction (2026-09-26):** use both `BOM-review.csv` and
`CPL-review.csv` from the local
`hw/releases/groundlark-daqhat-01-jlcpcb-placement-20260926-c91-c92/` overlay instead of
earlier BOM/CPL files. [Programmatic placement correction](assembly-placement.md)
audits all 117 placements against catalog pads and corrects 21 rotations in total.
C91/C92 now select KEMET C0603C102J5GAC7867 / C140950, an available catalog alias
with matching 1 nF / 50 V / C0G / ±5% / 0603 specification and a mapped footprint.
Gerbers are unchanged. Prior ZIPs are retained intact.
The corrected BOM has 38 catalog identities and 117 placements.
This is a BOM correction, not confirmation that JLCPCB can assemble every part.
It includes the J1 fix and [reviewed shortage replacements](assembly-shortages.md)
for C42/C80-C82, C84/C85, C90 and F80. F80 also corrects an old 0603 fuse MPN on
1206 PCB lands. The selected assembly MPN is now 0466005.NRHF / C57525.

The requested quantity is **ONE fabricated PCB and ONE assembled HAT**, the same
physical board. No increase to two or five is authorized. No order has been placed.
Export rejects every quantity except integer 1. The Gerbers contain one closed
85 x 56 mm outline, with no panel repeats. BOM/CPL and procurement totals describe
117 installed components on that one HAT. Package sealing checks these counts
again and writes `review/one-hat-quantity-check.json`.
The package is for quotation and engineering review, **not manufacturing release**.
The replacement export uses conventional six-layer FR-4 and retains the
Groundlark lark/waveform silkscreen. Exact working-tree hashes, rather than a
Git commit alone, identify the tested source. See [cost reduction](cost-reduction.md)
for supplier settings and the quote comparison. Full run
`20260926T052916Z-5c4e5ac3` passes all 22 stages (65 hardware and 187 software
regressions); native DRC/ERC/opens are zero. Earlier eight-layer HDI packages
are superseded and must not be uploaded as standard-process artwork.

## Files and scope

The current local review package at
`hw/releases/groundlark-daqhat-01-jlcpcb-review-20260926-one-hat/`
contains Gerbers, separate PTH/NPTH through-drill files, an assembly BOM, candidate
CPL, procurement quantities, via-processing coordinates, a four-page review PDF,
native Fab SVGs, independent Gerber views and validation evidence. Release directories are retained locally and ignored by Git; tools and intermediate
runs stay in `.local/`. Fabrication packages must not be committed or pushed
without an explicit request to publish them. Export tooling and tests remain tracked.

The assembled carrier has 117 placements and 38 BOM lines: 107 SMT-only, seven
THT-only and three mixed SMT/THT connectors. J80/J81/J82 have SMT signal contacts
and plated mounting features; they are no longer classified as THT-only. J1 is the bottom
Pi socket. The Raspberry Pi, Trenz TE0712 module, riser, geophone, supply, cooling
and mounting hardware are separate purchases; see the existing
[stack assembly](stack-assembly.md). The remote USB sensor head and deferred A2
Coldfoot board are not part of this package.

## What still prevents an order-ready package

1. **Quantity:** JLCPCB publishes a minimum of two Standard assembled boards.
   Supplier must accept a one-piece quote; increasing the order is prohibited.
   Bare PCB lot sizes, component purchase minimums and assembly losses are separate.
2. **Standard fabrication:** six-layer FR-4, nominal 1.6 mm, TG135, 1 oz outer /
   0.5 oz inner copper, ENIG, 0.30 mm through-drills, epoxy fill/capping (POFV).
   Use the stock JLC06161H-3313 reference; no HDI, custom lamination, controlled
   impedance, optional Kelvin testing or expedited lead time. The published
   stock copper/dielectric sum is 1.5384 mm; nominal 1.6 mm has +/-10% tolerance.
   CAD mask thickness is illustrative. Do not fill component PTH or NPTH holes.
3. **Assembly frame:** Standard PCBA requires edge rails and fiducials and has
   a 70 mm minimum dimension. The 85 x 56 mm HAT needs a manufacturer-proposed
   frame/panel. Approve the returned panel and retain the HAT outline and holes.
4. **Sourcing:** all 38 upload lines now have exact catalog identities. J1 selects
   [Megastar ZX-PM2.54-2-20PY / C7499354](https://jlcpcb.com/partdetail/ZX-PM2.54-2-20PY/C7499354),
   which is listed in JLCPCB's assembly catalog. Its 8.5 mm body is shorter than
   the original Samtec socket; stack/riser height and bottom-side orientation
   remain unresolved. The old Samtec 3D/fit evidence does not qualify this substitute.
   JP1/J4 are resolved to Samtec TSW-102-07-G-S /
   TSW-104-07-G-S; Q1 is Nexperia 2N7002,215. These procurement clarifications
   are recorded separately from the unchanged validated CAD. All stock
   allocations and assembly eligibility remain unconfirmed. Shortages for C90,
   F80 and six supply capacitors are addressed by the explicit selections in
   [assembly-shortages.md](assembly-shortages.md). JLCPCB showed available stock
   for these replacements; it has not been reserved. Do not omit them or accept further automatic substitutions.
   Signal capacitors must retain C0G dielectric, tolerance and voltage rating.
5. **Placement and process:** verify each JLC library rotation and centroid.
   Nine top connectors use catalog numbered-pad fits. Bottom J1 now uses an
   explicit C7499354 board-projection mapping at 0 degrees instead of 90.
   Thirteen additional IC/transistor/protection rotations are corrected, including
   U100/U101/U102/U103 on Bottom. C91/C92 now have exact C140950 catalog mappings
   and retain 0 degrees on Top. See [placement evidence and tests](assembly-placement.md).
   The front-layer J1 land pattern requires a **bottom-mounted socket**. Confirm
   mixed SMT/THT assembly, reflow/cleaning limits and sensor handling. JLC should
   populate required connectors too; this is not an SMT-only quote.

These are documented open issues, not waived checks. Passing simulation or DRC
does not close supplier-specific production details or physical qualification.

## Corrected BOM upload and matching

The previous returned supplier review matched R61 to a Zener diode, R96/R100-R105
to inductors, C12-C17 to 01005 capacitors, C90-C92 to X7R capacitors, and U40/D90
to unreviewed manufacturers. It also used five boards and omitted many parts
from its subtotal. Do not reuse that matching result or its price.

The exporter now reads [the exact-part registry](../hw/assembly/daqhat-01-jlcpcb-parts.json).
Each record binds the source MPN, value, footprint and references to the reviewed
manufacturer, ordering code, package and evidence URL. Changed source inputs,
missing selections, duplicate references, conflicting catalog identities and
undocumented resolutions fail export. The registry and exporter are hashed in
the release. A catalog identity is not stock reservation or assembly approval.

Upload `BOM-review.csv` as BOM and `CPL-review.csv` as placement data. Map:

| Upload field | Column in CSV |
| --- | --- |
| Comment / manufacturer part number | `Comment` (exact orderable MPN) |
| Designator | `Designator` |
| Footprint / package | `Footprint` (plain package name) |
| JLCPCB / LCSC part number | `JLCPCB Part #` (C-code) |

Manufacturer, MPN and description are also retained as supplementary columns.
The primary four columns are sufficient if the importer ignores extra fields.
Do not map `Description` as the ordering code. Confirm **38 nonblank catalog
codes, including C7499354 for J1,** survive the import. The three
identical jumper headers share one line. All 117 placements remain required.

For J1, match `C7499354` / `ZX-PM2.54-2-20PY` / `Megastar` in the order's
component-selection screen. This exact replacement is in the assembly registry;
do not reuse the older C21390538 BOM or mark J1 unplaced. It is a bottom-mounted
female socket with an 8.5 mm body. Its revised riser/spacer height and underside
orientation must be reviewed before assembly; the prior tall Samtec fit does not apply.

Set the supplier's **PCB quantity and assembled quantity to ONE** separately; BOM reference
counts describe one PCB and cannot control the website's quantity selector.
Procurement totals also target one HAT and exclude unknown MOQ/attrition.
Review manufacturer, full MPN, package, all allocations and the placement
preview before accepting. The CSV does not override supplier substitutions.

The correction adds 13 regression tests covering the real bad matches,
one-board quantities, missing/duplicate references, stale selections, manual
sourcing, primary upload fields and CSV quoting of `2N7002,215`. Four additional
tests reject batch export, repeated/open/multiple outlines and multiplied
procurement totals. All 82 hardware
tests pass. Fresh export DRC is clean; all 13 layers and 608 drill hits pass
independent parsing. Circuit, layout and CPL are unchanged from `imu-bypass`.

## Reproduce exports without changing CAD

Use KiCad 9.0.9 and a Python that imports `pcbnew` (WSL or the portable lab).
The exporter rejects source CAD/BOM hashes that differ from recorded validation,
checks all native DRC severities, validates the layer/drill inventory, and verifies
that BOM and CPL references agree. It refuses to overwrite a populated directory.

```bash
python3 hw/tools/jlcpcb_package.py --quantity 1 --output .local/jlcpcb/new-review
python3 -m unittest discover -s hw/tests -p 'test_jlcpcb*.py' -v
```

For optional independent plot inspection and PDF production, keep dependencies
inside the repo rather than installing into the atopile environment. The review
renderer uses rsvg-convert for luminance masks so silkscreen cutouts preserve
underlying copper, and draws the silkscreen above copper:

```bash

# Also requires rsvg-convert (librsvg2-bin on Debian/Ubuntu).
python3 -m venv --system-site-packages .local/fab-venv
.local/fab-venv/bin/pip install gerbonara==1.5.0 reportlab==4.4.10
.local/fab-venv/bin/python hw/tools/jlcpcb_inspect.py .local/jlcpcb/new-review
.local/fab-venv/bin/python hw/tools/jlcpcb_drawings.py .local/jlcpcb/new-review
```

The independent parser compares every exported hole location, diameter and
span to CAD (1 micrometre coordinate quantization), and parses all 13 plot layers.
The package report gives actual drill counts; no blind-drill files are accepted.
It emits benign parser warnings about KiCad's G90 header position and unused
RoundRect macro parameters; these are retained rather than suppressed. Render
the PDF with `pdftoppm` and inspect each page. Gerber parsing does not establish
DFM approval or validate solder-paste apertures against supplier process limits.

After adding the package README and reviewing the PDF, run
`python3 hw/tools/jlcpcb_seal.py .local/jlcpcb/new-review` to write checksums
and the complete review ZIP. This retains all manufacturing holds; it does not
promote the package to an approved release.

Electrical connectivity, sensor positions and axes are preserved. C12/C13/C16
placements and local SENS_3V3/GND copper changed for the bypass correction;
see [the IMU review](imu-placement-review.md). The full validation run is the
circuit/layout evidence. Independent export inspection parsed 13 layers and
matched 594 PTH plus 14 NPTH hits to CAD; all 533 vias are through-vias.
The four-page PDF was rendered and visually checked before sealing. Export integrity tests supplement that evidence.
Source hashes and output hashes must be regenerated if any file changes. Do not
reuse old upload files after a CAD, BOM, assembly-side or process change.

## Suggested quote request (draft only; not sent)

Please quote one assembled Groundlark DAQHAT-01 HAT, or confirm whether an exception
to the two-piece Standard PCBA minimum is available. The board is 85 x 56 mm,
standard six-layer FR-4, nominal 1.6 mm, ENIG, 1 oz outer / 0.5 oz inner copper,
0.30 mm through-drills with epoxy filling/capping, double-sided SMT plus THT.
Use stock JLC06161H-3313; no HDI or custom lamination. Please provide an
assembly handling-frame/fiducial proposal. All required connectors are to be
assembled, including bottom-mounted J1. Please identify sourcing/consignment,
MOQ/attrition and assembly-process constraints before quoting an order-ready BOM.
No substitutions, stack changes or manufacturing release are authorized by this
review package. Owner approval follows review of your proposed production data.

## Sources reviewed 2026-09-25

- [JLCPCB assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities):
  Standard service, two-piece minimum, panel dimensions, rails and fiducials.
- [PCB capabilities](https://jlcpcb.com/capabilities/Capab) and
  [six-layer POFV](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv).
- [KiCad 9 export guide](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9).
- [BOM format](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly)
  and [CPL format](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly).
- [Parts sourcing](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction).
- [LSM6DSOTR catalog](https://jlcpcb.com/partdetail/LSM6DSOTR/C2655100)
  and [TCA9534PWR catalog](https://jlcpcb.com/partdetail/TexasInstruments-TCA9534PWR/C783615).
