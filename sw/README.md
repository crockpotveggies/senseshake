# Software

The sensor HAT is driven by Pi software; it does not need separate MCU firmware.
The [active plan](../docs/sensor-development-plan.md) focuses on sensors using the
T1 FPGA stack; acquisition must run without Coldfoot or a configured FPGA.
These directories reserve clear ownership for the next implementation work:

- [pi/](pi/README.md): Pi device configuration, sensor drivers/adapters, acquisition,
  calibration and timestamps. Coldfoot host integration is deferred.
- [field-head/](field-head/README.md): microcontroller firmware for the remote
  USB-C magnetometer/infrasound board.
- [fpga/](fpga/README.md): Trenz pin/connectivity qualification and minimal test
  bitstreams; accelerator implementation is deferred.
- [tests/](tests/README.md): portable replay, fault injection and host integration.

No executable implementation is present in these directories yet. The existing
portable lab validates circuits, PCB connectivity and bounded SPICE models; it
does not simulate a Pi or enumerate the USB sensor head.
