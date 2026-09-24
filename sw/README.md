# Software

The sensor HAT is driven by Pi software; it does not need separate MCU firmware.
The [active plan](../docs/sensor-development-plan.md) focuses on sensors using the
T1 FPGA stack; acquisition must run without Coldfoot or a configured FPGA.
The sensor contracts and Pi acquisition application are executable:

- [interfaces/](interfaces/README.md): Protobuf schemas, semantic validation and bounded USB framing.
- [pi/](pi/README.md): Pi device configuration, sensor drivers/adapters, acquisition,
  calibration and timestamps. Coldfoot host integration is deferred.
- [field-head/](field-head/README.md): microcontroller firmware for the remote
  USB-C magnetometer/infrasound board.
- [fpga/](fpga/README.md): Trenz pin/connectivity qualification and minimal test
  bitstreams; accelerator implementation is deferred.
- [tests/](tests/README.md): portable replay, fault injection and host integration.

Run `./lab.ps1 test -Profile software` after rebuilding the portable image.
This checks schemas, compatibility, acquisition/replay, modeled bus drivers,
USB streams and recovery from injected faults. See the
[software run guide](../docs/sensor-software.md). USB-head firmware, FPGA test
bitstreams and physical qualification remain pending. Tests do not emulate
Pi/MCU instructions or enumerate a USB sensor head.
