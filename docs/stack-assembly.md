# T1-GEO bench assembly and cable fit

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

## Expansion cables: explicit outstanding fit work

J86/J87 have 40 contacts; J88/J89 have 60. The Amphenol F32Q connectors require
0.50 mm pitch and **0.30 +/-0.03 mm mating thickness**, with contacts on the
upper side of the connector. Because these connectors are on the underside,
the exposed mating contacts face away from the HAT, toward the Pi. A cable's
far-end contact side and pin order depend on the receiver. No receiver board
has been selected, so no complete off-the-shelf harness is approved here.

The `assembly_fit.py` calculation includes a candidate 150 mm custom flex
route: upper cables U-turn downward, lower cables S-drop, and all exit south.
Widths are 20.5 and 30.5 mm; the calculation reserves 0.5 mm lateral guide
allowance, 0.30 mm cable thickness and 1 mm vertical stack allowance. The
candidate leaves **2.029 mm** above the Pi's conservative 16 mm port envelope.
These are project routing assumptions, not supplier-certified bend limits.

Two findings prevent calling this a qualified four-cable assembly:

1. A straight J87 exit crosses the underside ADC bypass capacitors C95/C96.
   Its actual slot height, cable stiffener length and controlled downward exit
   must be checked together. The candidate path is deliberately reported as
   conditional; it is not represented as a collision-free installed cable.
2. The lower-right Pi spacer at (61.5,52.5) crosses the right cable corridor.
   A three-spacer bench arrangement avoids that corridor, but its stiffness
   needs a physical check. Keep all four spacers for the sensor-only prototype
   with these optional cables absent. Do not casually thread a flex around or
   clamp it under the fourth spacer.

Trim underside through-hole tails to at most 2 mm below the board. Insert
the flexes and close their latches before mounting the HAT on the Pi. Do not
fold a reinforced tip, force a cable against a capacitor, or connect an
unverified far end. GPIO continuity is preserved for all 155 exposed signals;
this does not establish loading or signal integrity for an arbitrary cable.

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
