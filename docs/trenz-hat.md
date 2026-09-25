# ShakeSense T1 — Pi-outline Trenz carrier

**Revision in planning:** the [internal FPGA link plan](fpga-host-link-plan.md)
replaces external GPIO ribbons with six QSPI-reserved wires, retained UART and
switched Pi-driven JTAG. The CAD and expansion details below remain the preceding
revision; these new connections are not yet implemented.

**T1-GEO revision:** GNSS is removed; one external Racotech vertical geophone
uses an ADS122C04 input. See [current circuit, acquisition and validation](geophone-input.md).
GNSS/PPS/RF details below describe the preceding revision or legacy recordings.
The current physical bench template is version 2, with geophone response/noise/timing
checks replacing the GNSS UTC check.

T1 is an **85 × 56 mm, eight-layer HDI** alternative to the A2 Coldfoot ASIC HAT.
Electrical source: [`hw/elec/hat_trenz.ato`](../hw/elec/hat_trenz.ato).
CAD: [`shakesense-trenz-hat.kicad_pcb`](../hw/boards/shakesense-trenz-hat/shakesense-trenz-hat.kicad_pcb).
The original ASIC HAT and remote USB sensor head remain separate builds.

## Stack and sensor placement

From bottom to top: Raspberry Pi, ShakeSense T1, **TE0712-03-81I36-A**.
The FPGA stays on top for heatsink access. The HAT keeps the four LSM6DSO IMUs,
SCL3300 inclinometer and ADS122C04 geophone input. The magnetometer and optional infrasound
sensor stay on the separate USB head; they consume no HAT area.

The Trenz outline occupies HAT coordinates x=30–80, y=8–48 mm, measured from
the upper-left corner. Its mounting holes are (33,11), (77,11), (33,45), (77,45)
mm. Two 100-contact connectors and one 60-contact connector mate underneath it.
The selected 4 mm carrier and module connectors give an **8 mm surface gap**.
Use four matching M3 spacers. Components under the module are low-profile;
the tall service connectors are outside its outline.

J1 retains the Samtec ESQ-120-23-G-D bottom socket. Its specified body height is
16.129 mm. A **Samtec SSQ-120-02-G-D** 1:1 GPIO riser now adds 8.51 mm between
the Pi and J1, giving **27.18 mm nominal Pi-top to HAT-underside clearance** with
a 2.54 mm Pi header base. Its 4.93 mm square tails point into J1; the socket face
mates to the Pi. Use measured spacers/shims for actual seating, without forcing
the connector stack. The conceptual model and assembly BOM include this riser.

This compact stack increases thermal and electrical coupling compared with
placing the FPGA beside the Pi. Accelerometer/tilt drift and noise must be
measured with the FPGA idle and active, and cooling must avoid exciting the
motion sensors. Pi cooler compatibility needs a physical check.

## Power and interfaces

**J83 requires an external regulated 3.3 V-class supply, not 5 V.** Pin 1 is positive;
pin 2 is ground. It powers Trenz VIN and 3.3VIN through F80, a 5 A fast fuse.
The Pi continues to supply the sensor circuit. Grounds are common; positive
supplies are separate. There is no new USB connector on the HAT.

Start with a current-limited supply capable of module startup. The initial
operating budget is 3 A; this is a design envelope, not a measured FPGA load.
Set **3.35 V ±0.5% at J83** and keep **3.201–3.399 V at the module management
supply under load**. The revised hot loop resistance budget is **30 mΩ total**,
including positive and ground paths, fuse, PCB and mating contacts. At 3 A this
leaves a calculated DC range of 3.243–3.367 V, before transients. This limit must
be verified by differential voltage measurements; no extracted or measured
resistance is claimed. Current-limit first startup and check inrush before raising
the limit. This prototype input still has no reverse-polarity or overvoltage
protection; those protections must be supplied by the external bench source.

The module's sequenced 3.3 V output powers the exposed FPGA banks and the B
side of the TXU0202 UART isolator. Pi GPIO25 enables that interface, with a
pull-down keeping it disabled at startup. GPIO17 asserts application reset
through an open-drain transistor; the supervisor also holds reset during a
low FPGA I/O supply. FPGA configuration reset is separate on JP81.

| Function | Module pin | Carrier pad |
| --- | --- | --- |
| Pi TX → FPGA UART RX | JM2-11, B14_L8_N | J81-12 |
| FPGA UART TX → Pi RX | JM2-13, B14_L8_P | J81-14 |
| Application reset, active low | JM2-14, B14_L10_N | J81-13 |
| Configuration reset | JM2-18 | J81-17 |
| JTAG TMS / TDI / TDO / TCK | JM2-93 / 95 / 97 / 99 | J81-94 / 96 / 98 / 100 |

Carrier/module connector numbering swaps odd and even pins. See the complete
[`trenz-pin-map.json`](trenz-pin-map.json). J84 is the accessible six-pin JTAG
header: **1 TMS, 2 TDI, 3 TDO, 4 TCK, 5 GND, 6 VREF**. VREF is a reference output,
not a power input. Use an external compatible JTAG programmer. R80 selects
FPGA JTAG by pulling JTAGEN low. JP80 disables module power sequencing when
shunted to ground. MODE and PGOOD are not used by host firmware in this revision;
NOSEQ has a defined low idle bias, but its behavior is CPLD-firmware-dependent.

J85 brings out three spare 3.3 V GPIOs. The UART service header is J4. The host
link remains 2 Mbaud UART. The existing Nexys Video bitstream does **not** work
unchanged: package pins, clocking and board reset handling must be ported and
validated for this module before use. Coldfoot accelerator work is deferred;
sensor acquisition must work without a configured FPGA.

## GPIO expansion

The carrier exposes **155 independent FPGA GPIOs**: the three existing J85
signals plus **152 new routes** through four underside FFC connectors. The
85 x 56 mm outline, sensor circuit, Pi UART/reset and JTAG connections remain.
Three of the module's 158 ordinary I/Os are reserved for the Pi UART and reset.

| FPGA bank | Total module I/O | Expansion connector | New GPIOs | Other contacts |
| --- | ---: | --- | ---: | --- |
| 13 | 30 | J86, 40 contacts | 30 | 9 grounds, 1 VREF |
| 14 | 30 | J87, 40 contacts | 24 | 15 grounds, 1 VREF |
| 15 | 50 | J88, 60 contacts | 50 | 9 grounds, 1 VREF |
| 16 | 48 | J89, 60 contacts | 48 | 11 grounds, 1 VREF |

Bank 14 also provides J85's three spares and the three reserved host signals.
The [complete GPIO contract](trenz-gpio-breakout.csv) lists every module pin,
carrier pad, bank, signal identity and expansion contact. The independent
[module GPIO fixture](trenz-gpio-module.csv) and [ground fixture](trenz-ground-module.csv)
were transcribed from the exact-SKU revision-03 schematic, page 6. Connector
mating swaps odd/even pad numbers. P/N pairs remain adjacent at the expansion
connector where both members are free; this is not a length-matching claim.

J86/J87 use **Amphenol F32Q-1A7H1-11040**; J88/J89 use
**F32Q-1A7H1-11060**. These are 0.5 mm-pitch, upper-contact ZIF connectors,
2 mm nominal height, on the **underside** of the HAT. Use matching 40/60-way
FFC/FPC cable and verify contact-side orientation against both connectors.
The two solder anchor tabs share the grounded mechanical pad (41 or 61);
that pad is not an extra cable contact.

On all four connectors, **pin 2 is the FPGA 3.3 V reference OUTPUT**; pins 1
and 3 are grounds. All unused cable contacts are grounds. Read GPIO contact
numbers from the CSV and the marked pad 1, not from an assumed ribbon view.
These are raw **3.3 V FPGA bank pins**, not 5 V-tolerant, isolated, ESD-protected,
or hot-pluggable ports. Do not power the HAT through VREF or externally drive
pins while the module is unpowered or configuring. External circuitry must
share ground and satisfy the selected FPGA I/O standard and sequencing.
Keep unused GPIOs as inputs until a pin-specific bitstream is qualified.

Attach cables before stacking. The revised 27.18 mm gap leaves **9.18 mm nominal
clearance** between a 2 mm underside connector and the modeled 16 mm Pi port.
Reserving 1 mm for cable envelope and 1 mm for combined seating/height tolerance
leaves **7.18 mm calculated margin**. These allowances are engineering targets,
not supplier tolerance certification. Cable bends/exits, the actual Pi cooler,
solder protrusions and mounting hardware still need an assembly trial.
Route cables clear of the Pi socket and standoffs; a final harness has not been
specified or qualified. Models show connector envelopes without installed cables.

The audit also corrected two old ground assignments: **JM1.12 is ETH_RD_N**
and is now disconnected; **JM1.31 is B16_L22_P** and now reaches J89. It added
missing ground contacts JM1.8/.26/.84 and disconnected unused JM2.29/.30.
The audit checks all 260 module connector signal contacts, including pins that
must stay isolated, rather than checking only the newly exposed GPIOs.

Ethernet PHY pairs, GTP lanes, dedicated clocks, internal memory and module
management pins are not GPIO expansion ports. Bank supplies are unchanged.
No Coldfoot accelerator implementation is included in this revision.

Sources: [exact-SKU schematic, page 6](vendor/trenz/SCH-TE0712-03-81I36-A.PDF),
[Trenz reference manual](https://wiki.trenz-electronic.de/display/PD/TE0712+TRM),
[40-contact connector](https://www.amphenol-cs.com/product/f32q1a7h111040.html),
[60-contact connector](https://www.amphenol-cs.com/product/f32q1a7h111060.html).

## Fabrication stack

The complete GPIO breakout uses a provisional **eight-layer 1+6+1 HDI** stack.
Ground planes are on In2.Cu and In5.Cu. Track width/clearance remain 0.15 mm;
small through vias use 0.45 mm pads / 0.20 mm drills. Outer-layer microvias use
0.30 mm pads / 0.10 mm laser holes and connect only F.Cu–In1.Cu or In6.Cu–B.Cu.
Via-in-pad microvias require filling and planarization. Nominal board thickness
is 1.6 mm, with 0.08 mm outer dielectrics. These values are explicitly recorded
in the native PCB and `hw/layout-trenz.json`.

This is a more expensive manufacturing process than the original carrier.
The fabricator must approve the complete stack, drill separation, fill/cap process
and materials; fabrication approval is the project owner's responsibility.
The GNSS trace is now **0.388 mm wide**, calculated as **49.98 Ω** using the
recorded 0.215 mm depth to In2.Cu, 35 μm copper and dielectric constant 4.3.
The route was shifted away from a via antipad, and 900 points under the RF copper
are checked for continuous ground. The analytical model excludes solder mask,
launches and dielectric variation: update it if stack properties change. This
closes the carried-over-width error, not RF measurement qualification.
Reducing GPIO count is the main available scope reduction; Ethernet is already
excluded and adds no routing burden.

## Verification and release limits

The delivered board passed:

- atopile compilation and explicit numeric constraint solving;
- compiled physical-pin comparisons, all 158 ordinary GPIO mappings and all
  260 module contacts, plus sensor-net preservation and mounting/header geometry;
- nine GPIO regression cases: valid circuit, six injected wiring faults,
  duplicate-pad identifier repair and preservation of project design rules;
- native KiCad ERC and DRC: **0 findings, 0 unconnected items**;
- a clean placement/import rebuild with all **5,316 tracks/vias identical** to
  the delivered native copper, including **37 microvias**, and zero DRC/open nets;
- fourteen bounded ngspice support checks: six revised DC power budgets, one
  expected undervoltage detection, three UART RC cases and four load-step cases.
- RF geometry/return-plane, Pi IRQ/PPS mapping and revised stack-margin checks;
  see [engineering closure](t1-engineering-closure.md).

Power copper was widened using DRC-checked trials and supplemented with front/
back pours and parallel vias. This does not establish ampacity, transient supply
performance, RF impedance, thermal behavior or EMC. No FPGA silicon simulation,
bitstream implementation or physical board test was performed for T1.
**Engineering prototype; not fabrication released.** Machine-readable results
are in [`validation.json`](../hw/boards/shakesense-trenz-hat/validation.json),
[`engineering.json`](../hw/boards/shakesense-trenz-hat/engineering.json) and
[`hw/simulation/trenz/results.json`](../hw/simulation/trenz/results.json).

## 3D artifacts

- [`3d.png`](../hw/boards/shakesense-trenz-hat/3d.png): actual carrier PCB.
- [`3d-bottom.png`](../hw/boards/shakesense-trenz-hat/3d-bottom.png): underside GPIO
  connectors, shown with simplified 2 mm component envelopes.
- [`trenz-mounted.png`](../hw/boards/shakesense-trenz-hat/trenz-mounted.png): carrier
  with the manufacturer's revision-03 Trenz STEP model.
- [`pi-trenz-stack-concept.png`](../hw/boards/shakesense-trenz-hat/pi-trenz-stack-concept.png):
  all three boards; the Pi and spacer bodies are explicitly simplified envelopes.
- [`stack-exploded.png`](../hw/boards/shakesense-trenz-hat/stack-exploded.png):
  conceptual separated view for inspecting all three levels.

The adjacent assembly `.kicad_pcb` files contain visualization-only models and
are not fabrication boards. Only `shakesense-trenz-hat.kicad_pcb` is the carrier
electrical/layout artifact. Generic vendor geometry is not tolerance signoff.

## Rebuild

From the repository root in WSL, with the optional local dependencies described
in the [build guide](build.md). Use the portable lab for routine validation.

```sh
CI=1 .local/atopile/bin/python -m atopile build -b trenz_hat hw
CI=1 .local/atopile/bin/python hw/tools/solve_constraints.py --target trenz_hat
python3 hw/tools/assemble_pcb.py --trenz
python3 hw/tools/import_routes.py shakesense-trenz-hat
python3 hw/tools/trenz_power.py
python3 hw/tools/widen_power.py shakesense-trenz-hat
python3 hw/tools/trim_dangling.py shakesense-trenz-hat
python3 hw/tools/review_schematic.py shakesense-trenz-hat
python3 hw/tools/check_trenz.py
python3 hw/tools/simulate_trenz.py
python3 hw/tools/trenz_models.py
python3 hw/tools/render_trenz.py
```

The supplied SES is a complete native-copper snapshot, including locked tracks
and HDI microvias. `import_routes.py` restores it; it is not a conventional
Freerouting result. Placement and circuit changes require native KiCad routing
and fresh validation. After completing changes, record the copper with:

```sh
python3 hw/tools/export_session.py shakesense-trenz-hat
```

The DSN is a connectivity/placement interchange artifact; the legacy autorouter
flow does not qualify or reproduce the HDI fabrication process. Keep the native
PCB, complete SES snapshot and pin contract synchronized.

`bootstrap_trenz.py` and `pack_trenz.py` record initial authoring/placement and
are **not routine rebuild steps**; they overwrite the maintained circuit/layout.
The local venv is recreated under `.local/atopile`; migrated legacy environments
are not part of the reproducible flow.

## Manufacturer references

- [Trenz TRM](https://wiki.trenz-electronic.de/display/PD/TE0712+TRM).
- [Revision-03 exact-SKU schematic](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/4x5/TE0712/REV03/Documents/SCH-TE0712-03-81I36-A.PDF).
- [Mechanical drawing](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/4x5/TE0712/REV03/Documents/DIM-TE0712-03.PDF).
- [Vendor STEP archive](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/4x5/TE0712/REV03/HW_Design/STP-TE0712-03-No%20Variations.zip).
- [CPLD behavior](https://wiki.trenz-electronic.de/display/PD/TE0712+CPLD).
- [Samtec Pi socket](https://www.samtec.com/products/esq-120-23-g-d).
- [Samtec riser family dimensions](https://suddendocs.samtec.com/catalog_english/ssw_th.pdf).
- [Microstrip equations](https://qucs.sourceforge.net/tech/node75.html).
- [Raspberry Pi 4 mechanical resources](https://pip.raspberrypi.com/categories/559-mechanical).

Vendor files in `docs/vendor/trenz` and `hw/models/trenz` retain their
manufacturer ownership; they document integration of a purchased module.
