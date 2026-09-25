# T1-GEO bench assembly and cable fit

**Previous revision:** this document describes the currently routed expansion
board. The [next revision plan](fpga-host-link-plan.md) removes the four flex
cables, J85-J89, cable guide and windowed spacer, restoring straight supports
after a new fit check. Current CAD/renderings have not yet been revised.

This defines the sensor-prototype assembly. The PCB is 85 x 56 mm. The Trenz
module stays above the HAT; the Pi stays below. CAD dimensions do not replace
first-article seating, cable strain or thermal measurements.

## Selected hardware

| Item | Selection | Fit rule |
| --- | --- | --- |
| Host | Raspberry Pi 4 Model B | This review does not cover Pi 5 or its active cooler. |
| Pi cooling | 18 x 18 x 10 mm heatsink from the official Pi 4 Case Fan kit | Heatsink only; allow 0.5 mm adhesive. Fan omitted. Thermal capacity remains to be measured under the intended workload. |
| Pi riser | Samtec SSQ-120-02-G-D plus existing ESQ-120-23-G-D | Nominal Pi top to HAT underside 27.179 mm; match spacer/shim height to seated connectors. |
| FPGA | TE0712-03-81I36-A, standard connectors | Nominal 8 mm module-to-HAT surface gap; exclude the low-profile version. |
| JTAG cable housing | Harwin M20-1060600, six M20-1180046 contacts | Single row, 2.50 mm wide, 15.44 mm long, 14 mm high. Mount on J84; take wires upward, then outward to the right. |
| Geophone plug | Phoenix Contact 1803581 | Mates J90; pins 1=GEO+, 2=GEO-, 3=shield/GND. |

The JTAG housing leaves **0.75 mm** to the module after a 0.5 mm lateral
allowance. Its lead must match J84's pin order, not a probe's default ribbon
order: **1 TMS, 2 TDI, 3 TDO, 4 TCK, 5 GND, 6 VREF**. Use the existing
[JTAG contract](trenz-hat.md); verify continuity before
power. Treat the probe's voltage-reference lead as a reference input, not a
second board supply.

The geophone plug's published 12.22 mm width is centred on the middle contact
at X=14.19 mm. Its right edge plus 0.5 mm allowance is X=20.80 mm, leaving
**9.20 mm** to the module. Reserve a vertical withdrawal column over J90 and
keep the cable to the left of X=25 mm, exiting the board's lower edge. Use
a shielded twisted pair with drain; clamp the jacket outside the board and
retain a relaxed service loop. Keep the external geophone vertical and
mechanically coupled to its measurement surface.

The service rendering uses conservative boxes for the plug and JTAG housing.
The plug box is deliberately above the entire header; its Z position is an
upper envelope, not an exact mating transform. It does not certify screwdriver
access or cable pull forces. Leave at least 25 mm unobstructed above that box
for service, and assemble/screw the geophone wires before plugging it in.

## Expansion cable clearance

The revised PCB moves **J87 from (17,39) to (17,36) mm** and **J83 from
(7,12) to (4.7,12) mm**. J87's downward cable exit now clears C95/C96; J83's
power-terminal tails are outside the left ribbon corridor. Sensor and analog
component placements remain fixed.

The south-right straight Pi spacer is replaced by the
[windowed spacer and insulating guide](../hw/mechanical/t1-ribbon-guide/README.md).
All four mounting points remain supported. The guide locates J86/J88 at
Z=-10.2 mm and J87/J89 at Z=-7.2 mm. The carrier is still 85 x 56 mm; only
the mechanical guide projects 2 mm beyond its south edge.

This arrangement requires **short-tip custom FPC tails**, not generic long
stiffener FFCs: <=0.15 mm flexible body, 0.30 +/-0.03 mm mating tips,
0.50 mm pitch, 20.5/30.5 mm width. Reinforcement may extend at most 0.5 mm
outside the latched housing. A 1 mm straight exit precedes 1.5 mm radius
static bends. The linked mechanical contract specifies manufacture, screws,
slot finishing, installation and the remaining receiver-end decisions.

`assembly_fit.py` checks inflated cable volumes against actual back-side
courtyards, all PTH tails, mounting screw heads and four Pi supports. It bounds
the unknown exact slot height using the entire 2 mm F32Q housing and checks
nine heights per connector. It also checks ribbon-to-ribbon separation and
spacer/guide clearance to the board. Regression tests reproduce the former
capacitor and straight-spacer collisions. The conservative clearance margins
are recorded in [prefab-review.json](../hw/boards/shakesense-trenz-hat/prefab-review.json).

The service render now includes the routed flex envelopes and actual spacer/
guide CAD. This closes the identified CAD interferences for the specified
assembly. Confirm the selected flex maker's tip and stackup drawing, then
measure first-article fit, strain relief and stiffness. No physical fit or
cable-fatigue test has been performed. These checks do not qualify arbitrary
expansion cables or high-speed GPIO loading.

## Analog assembly details

C90 is on the front beside U22. C95/C96 and D90 are on the back; check the
assembly side in placement exports. ADC supply-pin through-vias are via-in-pad:
include them in the filled/planarized/capped via schedule along with the
existing HDI requirements. Tenting alone is not a substitute for filling a
via under a solderable lead pad. Recheck solder paste and assembly drawings
when preparing the fabrication package.

## Sources and evidence

- [Pi 4 Case Fan product brief](https://datasheets.raspberrypi.com/case-fan/case-fan-product-brief.pdf)
- [Harwin M20-1060600](https://www.harwin.com/products/M20-1060600)
- [Phoenix Contact 1803581](https://www.phoenixcontact.com/en-us/products/pcb-plug-mc-15-3-st-381-1803581)
- [Amphenol F32Q/F32R datasheet](https://www.amphenol-cs.com/media/wysiwyg/files/documentation/datasheet/flex/ffc_fpc_050mm_f32r_f32q.pdf)
- [Amphenol FFC/FPC presentation: mating thickness](https://www.amphenol-cs.com/media/wysiwyg/files/documentation/customerpresentation/aorora_ffcfpc_productpresentation.pdf)
- [Measured board and selected-envelope report](../hw/boards/shakesense-trenz-hat/prefab-review.json)

The [pre-fab review](pre-fab-review.md) and [bench procedure](bench-procedure.md)
retain acquisition, noise, power and physical-fit qualification separately.
