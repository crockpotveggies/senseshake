# DAQHAT-01 three-IMU revision

**Superseded population:** the dedicated inclinometer has now been removed.
See [the current revision](inclinometer-removal.md). The figures below describe
the earlier three-IMU-plus-inclinometer design/research.


The active six-layer HAT now fits **three LSM6DSOTR IMUs: U11, U12 and U13**.
Each device measures all three acceleration axes. Their positions and orientation
are unchanged. The SCL3300 inclinometer, ADS122C04 geophone input and all FPGA
SPI/QSPI, UART and switched JTAG connections remain fitted.

## Circuit and layout

- Removed U14, its C18/C19 supply bypass capacitors and R14 chip-select pull-up.
- Removed the IMU4_CS/INT and PI_IMU4_CS/INT routes; trimmed disconnected branches
  of the shared SPI/supply copper and refilled planes.
- Grounded unused input U41.8 and U42.17. Their outputs U41.16/U42.7 are NC.
- J1 pins 31 (BCM6) and 18 (BCM24) are now unconnected spare Pi contacts, without
  a connection to the FPGA. No new function is assigned to them.
- Retained the 85 x 56 mm outline and stock six-layer FR-4/filled through-via rules.
- Current fitted BOM: **123 placements, 40 grouped MPN lines**. The three removed
  passives shared MPNs with retained parts, so feeder type count stays the same.

## Acquisition and compatibility

Current on-HAT IDs are **1, 2, 3, 5 and 9**. ID 4 retains its legacy IMU meaning;
no protobuf tags or historical compatibility baseline were changed. Legacy
recordings and explicit legacy simulation continue to support the fourth IMU.
New acquisition and UI simulations do not advertise or poll it.

The Pi overlay now has four SPI devices: IMU1/2/3 on spidev0.0/0.1/0.2 and
the inclinometer (still ID 5) on spidev0.3. Chip selects are BCM8/7/5/13;
IMU IRQs are BCM27/22/23. Use the updated example profile and overlay together.
An older five-device live profile is rejected before opening hardware.

The modeled signal bench checks all three IMUs, tilt and geophone through the
production drivers. Regression coverage includes the live inclinometer mapping,
legacy ID 4, rejected old profiles and rejected restoration of the removed parts.

## Assembly and cost

The older local `standard6` fabrication/assembly package contains four IMUs and
is superseded. **Regenerate a new local package before submission; do not upload
the old ZIP.** No release package was committed or pushed by this revision.

Savings are approximately $3.92 for the fourth IMU plus its three passives.
The revised one-HAT assembly budget is approximately **US$300-365**, including
the five-bare-PCB batch, before shipping, taxes and procurement extras. This is
an estimate using the previous setup allowance, not a fresh supplier quotation.
See [the itemized estimate](hat-cost-estimate.md).

Physical noise, calibration, power, timing and stack fit still require bench
qualification. Three independent equal-noise sensors ideally average to
1/sqrt(3) of one sensor's random noise; this is not measured performance.

Portable run `20260926T043013Z-f05318ce` passes all 22 stages, including 55
hardware and 188 software regressions. Native DRC/ERC/open counts are zero;
the routing replay reproduces all 11,116 copper objects exactly. Repository
structure and lab safety checks pass (one Windows-only safety case is skipped
inside Linux). The browser workbench passes 10/10 modeled signal checks with
3,464 samples and no gaps. HTTP/GLB/favicon and three-IMU inventory checks pass.

The independent before/after comparison checks 728 retained pads: component
positions/orientations are identical, only the six intended GPIO/buffer pin nets
change, and two private no-connect net names are regenerated. The BOM has 123
physical placements, plus 11 non-component footprints (holes/test pads/logo).

Evidence is in [verification.json](../hw/boards/groundlark-daqhat-01/verification.json).
Native renders and the workbench GLB are regenerated from the revised PCB;
the Pi/Trenz stack remains conceptual geometry.
