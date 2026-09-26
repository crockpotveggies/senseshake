# JLCPCB assembled DAQHAT-01 HAT

The requested quantity is **one assembled HAT**. No order has been placed.
The package is for quotation and engineering review, **not manufacturing release**.
The historical export preserves the circuit and routed PCB from commit `f4b84e4`.
It predates the Groundlark / DAQHAT-01 rename and is superseded: do not submit it.
Generate a fresh package from the renamed, validated source before quotation.

## Files and scope

The historical local review package at `hw/releases/t1-link-jlcpcb-review-20260925/`
contains Gerbers, separate PTH/NPTH/blind drill files, an assembly BOM, candidate
CPL, procurement quantities, via-processing coordinates, a four-page review PDF,
native Fab SVGs, independent Gerber views and validation evidence. One bounded
release directory is retained locally and ignored by Git; tools and intermediate
runs stay in `.local/`. Fabrication packages must not be committed or pushed
without an explicit request to publish them. Export tooling and tests remain tracked.

The assembled carrier has 127 placements: 117 SMT and 10 THT. J1 is the bottom
Pi socket. The Raspberry Pi, Trenz TE0712 module, riser, geophone, supply, cooling
and mounting hardware are separate purchases; see the existing
[stack assembly](stack-assembly.md). The remote USB sensor head and deferred A2
Coldfoot board are not part of this package.

## What still prevents an order-ready package

1. **Quantity:** JLCPCB publishes a minimum of two Standard assembled boards.
   One needs an exception quote; the user has not agreed to increase the order.
   Bare PCB lot sizes, component purchase minimums and assembly losses are separate.
2. **HDI stack:** the eight-layer 1+6+1 stack is provisional. Obtain an approved
   stack drawing with dielectric and finished copper thicknesses, material,
   tolerances, laser spans and filled/capped processing. The package proposes
   filling/capping every through-via conservatively; do not fill component holes.
   Any changed stack needs electrical/mechanical review before a release.
3. **Assembly frame:** Standard PCBA requires edge rails and fiducials and has
   a 70 mm minimum dimension. The 85 x 56 mm HAT needs a manufacturer-proposed
   frame/panel. Approve the returned panel and retain the HAT outline and holes.
4. **Sourcing:** the source BOM still uses descriptions instead of ordering codes
   for JP1 and J4; Q1 needs an exact manufacturer/ordering code. Most catalog
   mappings and all stock allocations remain unverified. LSM6DSOTR/C2655100 and
   TCA9534PWR/C783615 are recorded exact matches, not reserved supply. Do not map
   SCL3300-D01-10 to the different -1 consignment listing automatically. Samtec
   connectors may need global sourcing or consignment. Signal capacitors must
   retain their specified C0G dielectric, tolerance and voltage rating.
5. **Placement and process:** verify each JLC library rotation and centroid.
   CPL angles are raw KiCad CCW orientations; no unverified rotation corrections
   have been guessed. THT centres are pad-pattern estimates for manual review.
   The front-layer J1 land pattern requires a **bottom-mounted socket**. Confirm
   mixed SMT/THT assembly, reflow/cleaning limits and sensor handling. JLC should
   populate required connectors too; this is not an SMT-only quote.

These are documented open issues, not waived checks. Passing simulation or DRC
does not close supplier-specific production details or physical qualification.

## Reproduce exports without changing CAD

Use KiCad 9.0.9 and a Python that imports `pcbnew` (WSL or the portable lab).
The exporter rejects source CAD/BOM hashes that differ from recorded validation,
checks all native DRC severities, validates the layer/drill inventory, and verifies
that BOM and CPL references agree. It refuses to overwrite a populated directory.

```bash
python3 hw/tools/jlcpcb_package.py --quantity 1 --output .local/jlcpcb/new-review
python3 -m unittest discover -s hw/tests -p 'test_jlcpcb_package.py' -v
```

For optional independent plot inspection and PDF production, keep dependencies
inside the repo rather than installing into the atopile environment:

```bash
python3 -m venv --system-site-packages .local/fab-venv
.local/fab-venv/bin/pip install gerbonara==1.5.0 cairosvg==2.8.2 reportlab==4.4.10
.local/fab-venv/bin/python hw/tools/jlcpcb_inspect.py .local/jlcpcb/new-review
.local/fab-venv/bin/python hw/tools/jlcpcb_drawings.py .local/jlcpcb/new-review
```

The independent parser compares all 456 exported hole locations, diameters and
spans to CAD (1 micrometre coordinate quantization), and parses all 15 layers.
It emits benign parser warnings about KiCad's G90 header position and unused
RoundRect macro parameters; these are retained rather than suppressed. Render
the PDF with `pdftoppm` and inspect each page. Gerber parsing does not establish
DFM approval or validate solder-paste apertures against supplier process limits.

After adding the package README and reviewing the PDF, run
`python3 hw/tools/jlcpcb_seal.py .local/jlcpcb/new-review` to write checksums
and the complete review ZIP. This retains all manufacturing holds; it does not
promote the package to an approved release.

No electrical inputs or route geometry changed, so the prior full hardening run
remains the circuit evidence. Export integrity tests supplement that evidence.
Source hashes and output hashes must be regenerated if any file changes. Do not
reuse old upload files after a CAD, BOM, assembly-side or process change.

## Suggested quote request (draft only; not sent)

Please quote one assembled Groundlark DAQHAT-01 HAT, or confirm whether an exception
to the two-piece Standard PCBA minimum is available. The board is 85 x 56 mm,
eight-layer 1+6+1 HDI, nominal 1.6 mm, ENIG, double-sided SMT plus THT. Please
review the provisional stack and via-fill/capping proposal; provide a supported
stack and handling-frame/fiducial proposal. All required connectors are to be
assembled, including bottom-mounted J1. Please identify sourcing/consignment,
MOQ/attrition and assembly-process constraints before quoting an order-ready BOM.
No substitutions, stack changes or manufacturing release are authorized by this
review package. Owner approval follows review of your proposed production data.

## Sources reviewed 2026-09-25

- [JLCPCB assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities):
  Standard service, two-piece minimum, panel dimensions, rails and fiducials.
- [HDI capabilities](https://jlcpcb.com/help/article/hdi-pcb-capabilities-faq):
  laser vias, supported spans/processes and published geometry limits.
- [KiCad 9 export guide](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9).
- [BOM format](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly)
  and [CPL format](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly).
- [Parts sourcing](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction).
- [LSM6DSOTR catalog](https://jlcpcb.com/partdetail/LSM6DSOTR/C2655100)
  and [TCA9534PWR catalog](https://jlcpcb.com/partdetail/TexasInstruments-TCA9534PWR/C783615).
