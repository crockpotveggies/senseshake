# Software

The sensor HAT is driven by Pi software; it does not need separate MCU firmware.
These directories reserve clear ownership for the next implementation work:

- [pi/](pi/README.md): Pi device configuration, sensor drivers/adapters, acquisition,
  calibration, timestamps and the Coldfoot host runtime.
- [field-head/](field-head/README.md): microcontroller firmware for the remote
  USB-C magnetometer/infrasound board.
- [fpga/](fpga/README.md): Trenz board integration, constraints and bitstream flow.
- [tests/](tests/README.md): portable replay, fault injection and host integration.

No executable implementation is present in these directories yet. The existing
portable lab validates circuits, PCB connectivity and bounded SPICE models; it
does not simulate a Pi or enumerate the USB sensor head.
