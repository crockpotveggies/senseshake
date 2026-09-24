# Sensor development on the FPGA stack

## Active scope

Develop and validate sensor acquisition using the Raspberry Pi → T1 sensor HAT
→ Trenz TE0712 stack. The Pi owns acquisition and processing for this phase.
The application must also work with simulated sensors and with the FPGA absent
or unconfigured. No Coldfoot chip, runtime integration, or Coldfoot RTL port is
required for these milestones. Preserve the A2 ASIC design as deferred work.

On-HAT sensors are the four LSM6DSO IMUs, SCL3300 inclinometer, and MAX-M10S GNSS.
The RM3100 magnetometer and optional DLVR infrasound input remain on the separate
USB-C sensor head. Its MCU needs firmware; the accelerometer HAT does not.

Maintain the 85 × 56 mm T1 outline and the Pi/HAT/Trenz stacking arrangement.
Preserve the FPGA power, programming, reset and existing host/GPIO connections,
with 155 available Trenz GPIOs exposed on J85-J89. See the
[hardware pin contract](trenz-gpio-breakout.csv) and [carrier limits](trenz-hat.md).
This is a connectivity requirement, not an accelerator software dependency.

## Implementation checkpoint (2026-09-24)

The hardware prerequisite is committed and pushed as `3ff4111`.
Step 1 now has the [v1 contract](sensor-contract.md), Protobuf/Buf compatibility
checks, bounded USB framing, semantic validators and independent wire fixtures.
The portable software profile runs the executable contract tests. Nanopb has
candidate allocation bounds and a RAM budget assessment; C interoperability,
ARM/USB linked-image sizing and stack measurements remain open before firmware
selection. Steps 2–4 have not been implemented. The next work is Pi acquisition
with real/simulated adapters, session/configuration ordering and recording/replay.

## 1. Define sensor data contracts

- Define sensor samples/batches, acquisition configuration, device identity,
  status and errors in versioned Protobuf schemas under `sw/interfaces/`.
- Use Buf to check schemas and detect structurally incompatible changes.
- Specify units, raw versus calibrated values, coordinate axes, sample rate,
  acquisition timestamp clock/epoch, sequence numbers, reset epochs, validity,
  saturation and dropped-sample counts. Preserve the original sensor precision.
- Set explicit message/batch/buffer limits. Define framing and resynchronization
  for the USB CDC byte stream separately from the message schema.
- Keep semantic rules in the existing interface documentation and independent
  examples/tests. Evaluate Nanopb for the USB head against its actual RAM/flash
  budget; use JSON Schema only where human-editable configuration needs it.

**Exit gate:** independently written producer/consumer fixtures agree on valid,
invalid, missing and saturated sensor data; timestamp domains cannot be confused
with USB arrival time. No accelerator-specific message is required.

## 2. Implement Pi acquisition with real and simulated adapters

- Build sensor acquisition/configuration, calibration, timestamp handling,
  recording and replay under `sw/pi/`.
- Keep processing separate from Linux I2C/SPI/UART/USB access. Simulated adapters
  feed the same application with deterministic fixtures and recorded samples.
- Support the on-HAT sensors first, then the remote USB sensor stream.
- Use bounded queues and visible device/data-loss status. Sensor startup must
  not wait for an FPGA bitstream, accelerator response or Coldfoot chip.

**Exit gate:** the actual Pi application runs on the development machine against
simulated devices and produces repeatable, correctly timestamped recordings.
Real bus adapters are verified against hardware when boards are available.

## 3. Harden sensor acquisition and recovery

- Inject disconnected sensors, NACKs/timeouts, truncated or malformed messages,
  timestamp wrap/reset/jumps, dropped and duplicate samples, saturation, queue
  overflow, slow consumers, USB disconnects and reconnects.
- Specify recovery actions, retry limits, bounded memory use and how gaps are
  exposed. Do not silently replace missing measurements with apparently valid
  values or reorder samples across reset epochs.
- Test schema compatibility and replay against independently specified results.
- Add a software profile to the existing portable lab. Keep generated fixtures,
  logs and traces in its bounded disposable workspace.

**Exit gate:** expected failures produce defined status and recovery, preserve
valid sample ordering, and cannot hang acquisition or grow queues without bound.
This is application testing with modeled devices, not full Pi/MCU emulation.

## 4. Bring up the sensor hardware and qualify FPGA connectivity

- Implement the USB-head MCU firmware and check sensor acquisition, USB framing,
  enumeration, suspend/resume and reconnect behavior on actual hardware.
- Verify Pi-to-sensor access, sampling configuration, calibration and timing on
  the assembled T1 carrier. Measure sensor noise/drift with the FPGA unpowered,
  idle and active, including cooling-induced vibration.
- Audit each required FPGA connection from the Pi/header endpoint through the
  carrier connector to the module pin, including voltage domain, direction,
  reset/boot behavior, grounds and cable/programmer access.
- Qualify the implemented J85-J89 GPIO breakout with a physical cable/stack
  assembly trial and continuity tests. Verify 3.3 V sequencing, actual loading
  and edge rates; preserved P/N identities do not establish high-speed timing.
- Verify power sequencing, rail limits, no unintended back-powering, JTAG access
  and physical clearances. Use a small, pin-specific GPIO/UART test bitstream
  when useful; never blanket-drive unknown or power/control pins.

**Exit gate:** sensors operate on the real stack, the agreed FPGA connections
have documented CAD and bench evidence, and power/fit/thermal/noise findings are
resolved or explicitly block fabrication release. No Coldfoot port is required.

## FPGA GPIO hardware prerequisite

The updated carrier preserves Pi UART/reset, configuration controls and JTAG,
and exposes **155 available ordinary FPGA I/Os** through J85-J89. The new J86-J89
underside connectors add 152 signals. The remaining three of the module's 158
ordinary I/Os serve Pi UART and application reset. UART/reset have support
circuitry rather than being unrestricted passive wires.

Use the [GPIO pin contract](trenz-gpio-breakout.csv),
[carrier expansion audit](trenz-hat.md#gpio-expansion) and
[module-to-carrier pin map](trenz-pin-map.json) when defining test fixtures.
The GPIO contract identifies banks 13/14/15/16 and 3.3 V wiring; it does not
provide FPGA package-ball constraints or a validated bitstream. Produce those
from the exact module schematic when adding the small connectivity test design.

Ethernet PHY pairs, GTP transceivers, dedicated clocks, supply and management
pins are excluded. Keep bank supplies unchanged. Bench qualification still
includes FFC cable fit, startup behavior, loading and actual signal timing.
Passing continuity checks does not establish high-speed performance.

The first development milestone is completion of steps 1–3: robust sensor
software exercised without physical boards or accelerator dependencies.
