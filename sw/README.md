# Software

The sensor HAT is driven by Pi software; it does not need separate MCU firmware.
The [active plan](../docs/sensor-development-plan.md) focuses on sensors using the
T1 FPGA stack; acquisition must run without Coldfoot or a configured FPGA.
The initial sensor contract and framing implementation are now executable:

- [interfaces/](interfaces/README.md): Protobuf schemas, semantic validation and bounded USB framing.
- [pi/](pi/README.md): Pi device configuration, sensor drivers/adapters, acquisition,
  calibration and timestamps. Coldfoot host integration is deferred.
- [field-head/](field-head/README.md): microcontroller firmware for the remote
  USB-C magnetometer/infrasound board.
- [fpga/](fpga/README.md): Trenz pin/connectivity qualification and minimal test
  bitstreams; accelerator implementation is deferred.
- [tests/](tests/README.md): portable replay, fault injection and host integration.

Run `./lab.ps1 test -Profile software` after rebuilding the portable image.
This checks schemas, compatibility, data semantics and stream framing. Pi drivers,
acquisition/replay, USB-head firmware and the FPGA test bitstream are still pending.
These tests do not emulate a Pi or enumerate a USB sensor head.
