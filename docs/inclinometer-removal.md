# DAQHAT-01: remove the dedicated inclinometer

The active HAT contains **three XYZ LSM6DSO IMUs (U11-U13) and one ADS122C04
geophone input (U22)**. The SCL3300 inclinometer is removed at the owner's
request. The external magnetometer/infrasound head and deferred A2 design
retain their existing circuits.

## Circuit and native CAD

- Remove U20, C20-C23 and R20; no replacement sensor is fitted.
- Remove TILT_CS, PI_TILT_CS, TILT_AEXT and TILT_DEXT and their copper. Trim
  disconnected branches on shared supply/SPI nets and refill ground planes.
- Ground unused U41.9 through the adjacent grounded input U41.8 and its existing
  ground stitch. U41.15 is deliberately unconnected.
- Pi pin 33 / BCM13 becomes spare and unconnected. BCM6/24 were already spare.
  None of these spare Pi pins is wired to the FPGA.
- Retain all other component positions and orientations, three independent XYZ
  IMUs, FPGA UART/SPI/QSPI/JTAG connections, geophone input and 85 x 56 mm outline.
- Retain the six-layer stock FR-4 stack and through-via fabrication rules.

The BOM now contains **117 fitted components / 39 grouped part lines**. This
removes one unique sensor type and five passives. It saves approximately
**US$38.38 plus the passives** against the preceding three-IMU design, using
the existing price snapshot. The revised planning total for one assembled HAT
plus the minimum five-bare-board batch is **$262-327**, excluding shipping,
taxes and procurement extras. This is not a new supplier quote; see the
[itemized budget](hat-cost-estimate.md).

## Acquisition, UI and compatibility

Current HAT IDs are **1, 2, 3 and 9**. With the remote head, the workbench has six
sensors (adding IDs 7/8). The Pi overlay/profile expose only spidev0.0/0.1/0.2,
using BCM8/7/5. The geophone stays on I2C1 and IRQ assignments are unchanged.
Replace older deployed overlays/profiles together; a four-device live profile
is rejected before hardware opens.

Sensor IDs 4/5/6 and their protobuf fields retain legacy meanings. Old recordings,
the SCL3300 driver/model, and their compatibility tests remain available; current
acquisition never polls or advertises an inclinometer. The current UI has no
inclinometer card, pick target or fault selector.

The three IMUs already capture gravity as well as motion. They can support a
future calibrated stationary-level estimate. This revision **does not add or
claim a calibrated inclinometer replacement**: the workbench still displays raw
data. Each IMU remains an independent XYZ measurement, not a dedicated single axis.

## Verification and release

The modeled HAT signal experiment now covers three IMU drivers and the geophone
driver: 3,264 samples over eight seconds and nine checks. It retains known-roll,
gravity, gyro consistency, gain/frequency/phase, continuity and geophone checks.
Fault injection moves saturation from removed sensor 5 to active IMU1 so that
the current acquisition path continues to exercise saturation handling.

Portable run `20260926T045622Z-f0203bcf` passes all 22 stages, including 56
hardware and 187 software tests without skips. Native DRC/ERC/open counts are
zero; route replay reproduces 10,792 copper objects exactly. Lab safety checks
pass (one Windows-only case is skipped inside Linux). Repository structure and
UI HTTP/model/favicon checks pass. The browser shows 9/9 signal checks, 3,264
samples and zero gaps. A before/after comparison verifies 706 retained pads,
unchanged remaining positions/axes and only the three intended pin-net changes
(plus one renamed private no-connect net). Results are recorded in
[verification.json](../hw/boards/groundlark-daqhat-01/verification.json).
Physical power/noise/timing/stack qualification remains pending. The
[IMU placement review](imu-placement-review.md) identifies a bypass-loop cleanup
to address before considering the design noise-optimized.

**Previous local fabrication/assembly ZIPs are superseded.** Regenerate a new
local package from this revision before ordering. Releases remain ignored by
Git; this change does not place an order or publish a package.
