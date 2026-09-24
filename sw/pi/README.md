# Raspberry Pi software

Planned home for Pi device configuration, sensor bus adapters, acquisition and
calibration, timestamp handling, recording and replay. Sensor acquisition must
run independently of a configured FPGA. Follow the
[sensor development plan](../../docs/sensor-development-plan.md).

Separate pure processing/protocol logic from Linux I2C/SPI/UART/USB adapters so
the same application can run against recorded samples and fault-injecting fakes.
Use the [T1 sensor/carrier design](../../docs/trenz-hat.md) and
[USB interface contract](../../docs/usb-sensor-head.md). Coldfoot integration is
deferred; if resumed, its host semantics remain owned by the current
`docs/runtime_contract.md` in the separate Coldfoot SoC repository.

Implementation and software tests are pending.
