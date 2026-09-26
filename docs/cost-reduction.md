# DAQHAT-01 fabrication cost reduction

**Subsequent population change:** the active HAT now has three IMUs (U11-U13).
U14/C18/C19/R14 were removed; below, the 127-part/four-IMU comparison describes
the earlier six-layer conversion. See [current cost](hat-cost-estimate.md) and
[three-IMU revision](three-imu-revision.md).

Cost-reduction revision, 2026-09-25. Preserve all four IMUs, the inclinometer,
single Racotech geophone channel, Pi interfaces, QSPI reservation, UART,
JTAG switching, power isolation, module connectors and 85 x 56 mm outline.

## Why the previous PCB quote was expensive

The owner reported $212.46 for PCB fabrication alone, including a $99
engineering fee. The exact original quote breakdown is unavailable. The
previous released-for-review artwork used eight copper layers, eleven
0.1 mm laser-drilled blind microvias, and 283 mechanically drilled 0.2 mm
through-vias. It therefore required HDI processing: selecting
standard FR-4 in the checkout without rerouting is not a valid substitution.
HDI is a construction process; FR-4 is a laminate material, not its opposite.

The FPGA die is on the purchased Trenz module. The HAT does not need to
escape an FPGA BGA directly. Its dense IC escapes have been rerouted for
conventional through-vias. Two inner ground planes are retained.

## Supplier calculator comparison

Observed in the [JLCPCB quote calculator](https://cart.jlcpcb.com/quote) on
2026-09-25, without uploading Gerbers or placing an order:

| Setting | Standard-process comparison |
| --- | --- |
| Board | FR-4, six layers, 85 x 56 mm, single design |
| Quantity | Five bare PCBs; this does not change the requested assembled quantity |
| Thickness | 1.6 mm |
| Material | FR4 TG135 |
| Copper | 1 oz outer, 0.5 oz inner |
| Colour | Green solder mask, white silkscreen |
| Via processing | Epoxy filled and capped; through-vias only |
| Minimum via | 0.3 mm drill / 0.45 mm pad |
| Testing | Flying probe; no optional Kelvin test |
| Stack reference | JLC06161H-3313; selecting it retained the $49.10 ENIG price |
| Tolerances | Standard outline tolerance, no controlled-impedance order |
| Lead time | Standard, displayed as 8–9 days |
| OSP finish | $32.00 total for five bare PCBs |
| ENIG finish | $49.10 total: $32.00 base + $17.10 finish |
| Separate engineering fee | None displayed for these settings |

These are USD calculator estimates, **not a Gerber-validated quote**, and
exclude assembly, components, shipping and taxes. No coupon was applied.
The first $32 comparison used OSP; ENIG is the retained design finish.
The original quote's bare-board quantity is not independently known, so
these numbers should not be presented as verified like-for-like savings.

Selecting 0.2 mm holes in the calculator added fine-hole processing and
automatically selected Kelvin testing and Tg155 material. Selecting 1 oz
inner copper also added a charge. Avoid expedites: the displayed faster
lead times cost more than the baseline PCB batch itself.

## Fabrication rules for the six-layer revision

Use [JLCPCB's published capabilities](https://jlcpcb.com/capabilities/Capab)
and [POFV rules](https://jlcpcb.com/news/free-via-in-pad-6-20-layer-pcbs-pofv),
rather than treating KiCad defaults as a manufacturer's process specification:

- 0.3 mm mechanically drilled vias, 0.45 mm or larger pads; 0.075 mm
  annular ring is the supplier's preferred POFV ring.
- Target 0.125 mm signal tracks and 0.10 mm track clearance at dense
  escapes; preserve wider power conductors and the geophone layout.
- At least 0.20 mm via-hole-to-copper clearance and 0.20 mm via-hole spacing.
- At least 0.30 mm PTH drill-to-copper clearance and 0.45 mm spacing
  involving component holes. Copper-to-board-edge clearance stays 0.30 mm.
- SMD pad-to-pad clearance stays 0.15 mm. Both GND reference planes remain.
- Filled/capped vias remain necessary under solder pads; do not replace
  that with tenting simply to obtain a cheaper quote.

The promoted routing passes native DRC (zero errors/opens), connectivity
comparison against the compiled atopile circuit, analog path/return checks and
mechanical fit. Clean replay reproduces all 11,546 copper objects exactly.
Full portable run `20260926T034710Z-7502c956` passes all 22 stages, including
54 hardware regressions and 185 software tests. The 14 lab safety tests have
13 passes and one expected Windows-only skip in Linux. The workbench HTTP/GLB
smoke test passes; native top, bottom and stack renders were regenerated.
Fabrication exports must independently reject blind/buried/microvias,
unexpected layer spans, undersized drills and stale source hashes.

## Assembly and component costs

The existing physical BOM has 127 placements and 40 grouped BOM lines,
including 117 SMT-only, three mixed-mount Samtec connectors and seven
through-hole-only placements. The package's coarse THT classification includes
the mixed-mount connectors; include their SMT contacts in feeder/placement costs.
See the [component and assembly estimate](hat-cost-estimate.md). These costs are **not**
part of the reported $212.46. Removing sensors will not eliminate the
current fabrication process fee, so no sensor or interface is being removed.

For the next assembly quote, compare the complete setup/stencil/feeder,
double-sided placement, mixed SMT/THT, component procurement and shipping
breakdown. Resolve actual orderable header/transistor MPNs and stock
allocations before claiming a total assembled price. Prefer standard
assembly quantities over a bespoke one-piece exception only if the owner
chooses that tradeoff. No order or quantity increase has been authorized.

Disposable routing trials and their reports live under `.local/cost-down/`.
Existing fabrication packages remain immutable, local and ignored under
`hw/releases/`; they must not be used as standard-process artwork.

## Stock stack and preserved design

Stock reference JLC06161H-3313 uses copper thicknesses
0.035 / 0.0152 / 0.0152 / 0.0152 / 0.0152 / 0.035 mm and dielectric thicknesses
0.0994 / 0.55 / 0.1088 / 0.55 / 0.0994 mm. The supplier's copper/dielectric sum
is 1.5384 mm. Order 1.6 mm nominal (+/-10%); do not request custom lamination
to force an exact 1.600 mm sum. The 0.01 mm CAD masks and dielectric constants
are visualization/model assumptions. No controlled impedance is claimed.

The component inventory, footprints, pad nets, positions, sides and orientations
were compared against the saved eight-layer board and are unchanged. All 138
CAD footprints remain (127 physical placements, plus holes/test pads). Power
copper was widened with native DRC rollback; the broad front/back FPGA supply
paths remain. Via-in-pad processing is retained. Both GND reference planes and
the six geophone local-path/three ground-stitch limits pass. Changes in return
geometry still require physical noise and signal-integrity qualification.
