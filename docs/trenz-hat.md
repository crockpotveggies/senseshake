# ShakeSense T1 — Pi-outline Trenz carrier

T1 is an **85 × 56 mm, six-layer** alternative to the A2 Coldfoot ASIC HAT.
Electrical source: [`elec/hat_trenz.ato`](../elec/hat_trenz.ato).
CAD: [`shakesense-trenz-hat.kicad_pcb`](../hardware/shakesense-trenz-hat/shakesense-trenz-hat.kicad_pcb).
The original ASIC HAT and remote USB sensor head remain separate builds.

## Stack and sensor placement

From bottom to top: Raspberry Pi, ShakeSense T1, **TE0712-03-81I36-A**.
The FPGA stays on top for heatsink access. The HAT keeps the four LSM6DSO IMUs,
SCL3300 inclinometer and MAX-M10S GNSS. The magnetometer and optional infrasound
sensor stay on the separate USB head; they consume no HAT area.

The Trenz outline occupies HAT coordinates x=30–80, y=8–48 mm, measured from
the upper-left corner. Its mounting holes are (33,11), (77,11), (33,45), (77,45)
mm. Two 100-contact connectors and one 60-contact connector mate underneath it.
The selected 4 mm carrier and module connectors give an **8 mm surface gap**.
Use four matching M3 spacers. Components under the module are low-profile;
the tall service connectors are outside its outline.

J1 retains the Samtec ESQ-120-23-G-D bottom socket. Its specified body height is
16.129 mm, giving approximately **18.67 mm Pi-top to HAT-underside clearance**
with a 2.54 mm Pi header base. Use measured spacers/shims for the actual header
mating depth; do not force the connector to match an arbitrary spacer length.
The conceptual model uses this nominal stack with a 1.6 mm HAT PCB.

This compact stack increases thermal and electrical coupling compared with
placing the FPGA beside the Pi. Accelerometer/tilt drift and noise must be
measured with the FPGA idle and active, and cooling must avoid exciting the
motion sensors. Pi cooler compatibility needs a physical check.

## Power and interfaces

**J83 requires an external regulated 3.3 V supply, not 5 V.** Pin 1 is positive;
pin 2 is ground. It powers Trenz VIN and 3.3VIN through F80, a 5 A fast fuse.
The Pi continues to supply the sensor circuit. Grounds are common; positive
supplies are separate. There is no new USB connector on the HAT.

Start with a current-limited supply capable of module startup. The initial
operating budget is 3 A; this is a design envelope, not a measured FPGA load.
Keep **3.201–3.399 V at the module management supply under load**, including
fuse, wiring and PCB drop. There is no reverse-polarity or overvoltage protection
on this prototype input. The 15 mΩ fuse-plus-PCB resistance used in the budget
simulation is an acceptance target, not an extracted or measured result.

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
validated for this module before the Pi can use it as a Coldfoot accelerator.

## Verification and release limits

The delivered board passed:

- atopile compilation and explicit numeric constraint solving;
- 615 compiled physical-pin comparisons and 29 independently specified critical
  module pin checks, plus sensor-net preservation and mounting/header geometry;
- native KiCad ERC and DRC: **0 findings, 0 unconnected items**;
- ten bounded ngspice support checks: six DC power budgets, one expected
  undervoltage detection, and three 2 Mbaud UART RC-load cases.

Power copper was widened using DRC-checked trials and supplemented with front/
back pours and parallel vias. This does not establish ampacity, transient supply
performance, RF impedance, thermal behavior or EMC. No FPGA silicon simulation,
bitstream implementation or physical board test was performed for T1.
**Engineering prototype; not fabrication released.** Machine-readable results
are in [`validation.json`](../hardware/shakesense-trenz-hat/validation.json) and
[`simulation/trenz/results.json`](../simulation/trenz/results.json).

## 3D artifacts

- [`3d.png`](../hardware/shakesense-trenz-hat/3d.png): actual carrier PCB.
- [`trenz-mounted.png`](../hardware/shakesense-trenz-hat/trenz-mounted.png): carrier
  with the manufacturer's revision-03 Trenz STEP model.
- [`pi-trenz-stack-concept.png`](../hardware/shakesense-trenz-hat/pi-trenz-stack-concept.png):
  all three boards; the Pi and spacer bodies are explicitly simplified envelopes.
- [`stack-exploded.png`](../hardware/shakesense-trenz-hat/stack-exploded.png):
  conceptual separated view for inspecting all three levels.

The adjacent assembly `.kicad_pcb` files contain visualization-only models and
are not fabrication boards. Only `shakesense-trenz-hat.kicad_pcb` is the carrier
electrical/layout artifact. Generic vendor geometry is not tolerance signoff.

## Rebuild

From this project in WSL:

```sh
CI=1 .venv-atopile/bin/python -m atopile build -b trenz_hat .
CI=1 .venv-atopile/bin/python tools/solve_constraints.py --target trenz_hat
python3 tools/assemble_pcb.py --trenz
python3 tools/import_routes.py shakesense-trenz-hat
python3 tools/trenz_power.py
python3 tools/widen_power.py shakesense-trenz-hat
python3 tools/trim_dangling.py shakesense-trenz-hat
python3 tools/review_schematic.py shakesense-trenz-hat
python3 tools/check_trenz.py
python3 tools/simulate_trenz.py
python3 tools/trenz_models.py
python3 tools/render_trenz.py
```

The supplied SES matches `layout-trenz.json`. After changing placement or circuit,
reroute its exported DSN before importing:

```sh
xvfb-run -a java -jar tools/freerouting-1.9.0.jar \
  -de hardware/shakesense-trenz-hat/shakesense-trenz-hat.dsn \
  -do hardware/shakesense-trenz-hat/shakesense-trenz-hat.ses \
  -mp 10 -mt 1 -oit 20 -da
```

`bootstrap_trenz.py` and `pack_trenz.py` record initial authoring/placement and
are **not routine rebuild steps**; they overwrite the maintained circuit/layout.
The migrated venv entrypoint is invoked through Python to avoid old C: shebangs.

## Manufacturer references

- [Trenz TRM](https://wiki.trenz-electronic.de/display/PD/TE0712+TRM).
- [Revision-03 exact-SKU schematic](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/4x5/TE0712/REV03/Documents/SCH-TE0712-03-81I36-A.PDF).
- [Mechanical drawing](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/4x5/TE0712/REV03/Documents/DIM-TE0712-03.PDF).
- [Vendor STEP archive](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/4x5/TE0712/REV03/HW_Design/STP-TE0712-03-No%20Variations.zip).
- [CPLD behavior](https://wiki.trenz-electronic.de/display/PD/TE0712+CPLD).
- [Samtec Pi socket](https://www.samtec.com/products/esq-120-23-g-d).
- [Raspberry Pi 4 mechanical resources](https://pip.raspberrypi.com/categories/559-mechanical).

Vendor files in `docs/vendor/trenz` and `hardware/models/trenz` retain their
manufacturer ownership; they document integration of a purchased module.
