# Raspberry Pi software

Planned home for Pi device configuration, sensor bus adapters, acquisition and
calibration, timestamp handling, and accelerator host integration.

Separate pure processing/protocol logic from Linux I2C/SPI/UART/USB adapters so
the same application can run against recorded samples and fault-injecting fakes.
Use [the hardware integration notes](../../docs/coldfoot-integration.md) and
[USB interface contract](../../docs/usb-sensor-head.md). Coldfoot host semantics
must follow the current `docs/runtime_contract.md` in the separate Coldfoot SoC
repository; board documentation does not redefine that contract.

Implementation and software tests are pending.
