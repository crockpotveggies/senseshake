# IMU placement and noise review

Reviewed against the three-IMU/no-inclinometer native PCB; bypass update 2026-09-26 UTC.
The placement provides useful separation from major HAT power/digital circuitry,
but **minimum noise has not been established**. Passing DRC and ideal signal
tests does not validate thermal drift, vibration pickup or supply noise.

| Sensor | Center XY, mm | Center to FPGA outline, mm | Center to U40 regulator, mm | Nearest mounting-hole center, mm |
| --- | --- | ---: | ---: | ---: |
| U11 | 13, 24 | 17 | 61.2 | 22.6 |
| U12 | 24, 24 | 6 | 50.4 | 15.8 |
| U13 | 13, 36 | 17 | 60.0 | 19.0 |

Coordinates are measured from the HAT upper-left; the FPGA outline is
x=30-80, y=8-48 mm. All IMUs lie outside that outline, with matching axes.
These are planar geometric distances, not thermal or mechanical isolation.
The Pi remains beneath the assembly and shares its mechanical supports.

## Bypass-loop correction

Updated 2026-09-26 UTC. C12/C13/C16 were repositioned, C15 received a direct
supply connection, and U11/U12 received local ground stitching. Only SENS_3V3
and GND copper changed. All pad nets, sensor axes and other component positions
are preserved. No components were added to the BOM.

| Capacitor / assigned supply | Previous supply path, mm | Revised supply path, mm | Revised copper path to ground-plane via, mm |
| --- | ---: | ---: | ---: |
| C12 / U11 VDDIO (5) | 9.994 | 1.389 | 0.000 |
| C13 / U11 VDD (8) | 3.800 | 1.209 | 0.557 |
| C14 / U12 VDDIO (5) | 3.602 | 3.602 | 1.924 |
| C15 / U12 VDD (8) | 4.136 | 1.651 | 0.000 |
| C16 / U13 VDDIO (5) | 5.661 | 2.588 | 0.000 |
| C17 / U13 VDD (8) | 1.607 | 1.607 | 0.000 |

Zero means a ground via is directly inside the capacitor pad; it does not mean
zero impedance. The existing fabrication requirement for filled/capped
through-vias also applies to these new vias. Ground pins 6/7 now reach an
In1.Cu ground-plane via within 2.14 mm of tracked copper (worst of six pins).

`hw/tools/imu_layout.py` measures connected native track/via paths, permits
conduction across pad interiors, and verifies the return via intersects the
filled In1.Cu GND plane. Project geometry limits are 4 mm for VDDIO bypass
paths, 2 mm for VDD bypass paths, 2 mm for capacitor ground paths and 2.5 mm
for IMU ground-pin paths. These are review thresholds, not manufacturer
performance limits. Eight regressions check valid geometry, disconnection,
wrong value, DNP, missing/wrong-net ground stitching and excessive detours.
The check is part of the full portable lab's pre-fab review.

The earlier measurements used endpoint graphs without explicit pad-interior
bridging; both methods exclude via barrel length, pad spreading, plane
impedance and parasitic extraction. ST calls for 100 nF bypass capacitors
close to both supply pins.
[LSM6DSO datasheet, section 7.1](https://www.st.com/resource/en/datasheet/lsm6dso.pdf)

The sensor placements are retained: relocating them into the vacant area to
the right would put them beneath the FPGA module. The present positions keep
all three outside that outline, 50-61 mm from U40. There is no measured basis
to trade that separation for a new location closer to other heat sources or
mounting stresses. Local bypass routing is improved without that tradeoff.

This is not a quiet-zone guarantee. U102, the underside TCA9534 GPIO expander,
is 4.47 mm from U11 and 7.28 mm from U12 (center-to-center); U104, a voltage
supervisor, is 6 mm from U12. U22, the geophone ADC, is 8.06 mm from U13.
U102 carries control I2C rather than the main FPGA sample transport; U104 is
not a switching power converter. These neighbors and their edges can still
couple noise, so their activity belongs in the first-article measurements.
No electrical or mechanical noise reduction in dB is claimed from spacing.

## Mechanical, thermal and measurement follow-up

Review sensor support symmetry and board stiffness with the actual stack and
enclosure. ST identifies fasteners and asymmetric board stress as possible bias
sources, recommends locating sensors between supports, and advises separation
from heat sources. [ST TN0018, section 6](https://www.st.com/resource/en/technical_note/CD00134799.pdf)

Keep the sensors rigidly coupled to the intended seismic mounting surface;
uncharacterized soft isolation would alter the signal as well as vibration pickup.
Check cooler vibration, thermal settling, cable forces and mounting torque.
Measure stationary spectra, drift and cross-sensor correlation with the FPGA
off, idle and active, and with the intended cooling arrangement. Define the
frequency band and acceptable noise before interpreting results as a pass.

Three sensors can reduce independent random noise through synchronized,
calibrated averaging. Common board motion, thermal bias and electrical pickup
will not necessarily decrease. Current acquisition retains separate raw streams.
Sensor relocation was not required; the local bypass routing changes above are implemented.

## Recorded validation

Full portable run `20260926T052916Z-5c4e5ac3`: 22 stages passed, 65 hardware
and 187 software tests; native DRC/ERC/unconnected counts are zero. Replaying
the native SES preserves all 10,797 track/via objects exactly. Nine modeled
HAT signal checks pass; UI HTTP/GLB checks and native 3D render review passed.
The fresh local Gerber/assembly package is described in
[JLCPCB assembly preparation](jlcpcb-assembly.md). Physical qualification remains open.
