# Remote sensor-head firmware

Planned firmware for the USB-C board's microcontroller: magnetometer acquisition,
optional infrasound input, USB descriptors/transport, and recovery from resets
and disconnects. The authoritative interface is the existing
[USB sensor-head contract](../../docs/usb-sensor-head.md).

Firmware implementation, enumeration tests and physical USB validation are pending.
This firmware is separate from the Pi software that drives the accelerometer HAT.
