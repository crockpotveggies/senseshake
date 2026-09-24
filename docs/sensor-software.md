# Sensor acquisition and recovery

The runnable Pi application is in `sw/pi/senseshake/`; use
`sw/tools/sensor.py` as its repository entry point. It has no FPGA, Coldfoot,
network service or database dependency. Simulation and Linux device adapters
use the same scheduler, calibration, session validation and recording path.
This implements the development milestone in steps 1–3 of the
[sensor plan](sensor-development-plan.md). Physical acceptance remains step 4.

## Run without hardware

Run `./lab.ps1 test -Profile software` (or `sh ./lab.sh test --profile software`).
The portable environment contains the pinned Python/Protobuf and Buf tools.
It builds the descriptor, runs tests, executes a two-second eight-sensor fault
scenario and replays it. Retained outputs are under
`.lab/runs/<run-id>/results/sw/build/`: `demo.ssrec`, `demo-summary.json` and
`verification.json`. Five-run retention and existing cleanup cover these files.
No new environment or global package installation is needed for this workflow.

For direct development use Python 3.12+ with the Protobuf version in
`environment/requirements.lock`, and Buf 1.73.0. Generate the descriptor once:

```sh
mkdir -p sw/build
buf build sw/interfaces --exclude-source-info -o sw/build/schema.binpb
python sw/tools/sensor.py simulate --remote --seconds 2 \
  --faults sw/tests/fixtures/acquisition_faults.json --output sw/build/my-run.ssrec
python sw/tools/sensor.py replay sw/build/my-run.ssrec
```

Outputs use exclusive creation: choose a new filename for each direct run.
The lab manages its own copy and does not delete direct developer recordings.
`SENSESHAKE_DESCRIPTOR` can select a descriptor outside the default build
directory. Do not use the frozen compatibility baseline as the generated schema.

The scenario is deterministic for a given seed, configuration and fault file,
including recording bytes. It covers four IMUs, the inclinometer, GNSS,
magnetometer and pressure. Remote streams in this command are modeled MCU
producers, not firmware or USB emulation. Separate tests send framed messages
in fragments through a Linux pseudo-terminal. `--queue 1 --drain-every 100`
exercises a slow consumer. Simulated time starts at zero; Pi and remote clocks
retain distinct domains even when numerically equal.

## Linux device adapters

The live path uses Linux SPI/I²C ioctls, GPIO character-device line requests,
and a nonblocking USB CDC TTY. The initial profile is:

| Sensor | Configuration and reading |
| --- | --- |
| Four LSM6DSO | 26 Hz, ±2 g, ±250 dps; identity/reset/readback; BDU/address increment; signed temperature, gyro and acceleration. |
| SCL3300 | Mode 1, angle outputs enabled; startup/identity/mode readback; off-frame response/CRC checks; 25 Hz polling. |
| MAX-M10S | I²C 0x42; RAM-only UBX CFG-VALSET/ACK/VALGET; NAV-PVT every second; retain its complete 92-byte payload. |
| USB head | Receive v1 identity/configuration/batches/status over framed CDC; real firmware is still required. |

Copy [the example profile](../sw/pi/profiles/t1.example.json) and verify paths
on the actual Pi. `gpiochip0` is an example, not an assertion about Pi 5 GPIO
numbering. `line` is the character-device offset corresponding to BCM26 on that
chip. The application owns active-low sensor output enable and disables it on
normal/error cleanup.

| Signal | BCM GPIO | Physical header pin |
| --- | --- | --- |
| SPI0 MOSI / MISO / SCLK | 10 / 9 / 11 | 19 / 21 / 23 |
| IMU1 / IMU2 / IMU3 / IMU4 chip select | 8 / 7 / 5 / 6 | 24 / 26 / 29 / 31 |
| SCL3300 chip select | 13 | 33 |
| Sensor buffer OE, active low | 26 | 37 |
| GNSS I²C SDA / SCL | 2 / 3 | 3 / 5 |

**Deployment prerequisite:** configure the Pi device tree for all five SPI
chip-selects in that order and enable I²C1. The standard two-select setup is
insufficient. A board-specific overlay and verification on the selected
Pi/kernel remain bring-up work; none is auto-installed here. Bind sensor
devices to `spidev` using the kernel's documented `driver_override` mechanism
where needed. Do not run a kernel sensor driver and this polling driver against
the same device. Grant access to the selected SPI/I²C/GPIO/TTY devices.

```sh
python sw/tools/sensor.py live --profile sw/pi/profiles/t1.example.json \
  --seconds 60 --output sw/build/bench-001.ssrec
# Add --usb /dev/serial/by-id/<actual-head-id> when head firmware is ready.
```

Startup fails closed: every local sensor must identify and confirm settings
before effective-configuration advertisements. Live boot IDs are random per
acquisition process. The application never accesses FPGA UART, JTAG, reset or
GPIO expansion.

These drivers have modeled-bus verification, not bench qualification. Polling
timestamps represent read completion using `CLOCK_MONOTONIC_RAW`; conversion
uncertainty and physical overwritten-conversion counts are unknown. Live
batches omit `dropped_before`. Sequences count scheduled application slots;
overdue slots are skipped and unavailable scheduled samples are MISSING.
Do not infer lossless acquisition or synchronized devices from polling time.
FIFO/interrupt acquisition, PPS/UTC correlation, sensor self-test qualification,
board-axis transforms and GNSS fix decoding remain follow-on work. SCL3300
register reads are sequential, not an atomic six-axis snapshot.

## Recovery and bounds

Each local device runs in one supervised process with one outstanding request.
A read deadline is 250 ms; configuration has four seconds. Termination and kill
each get a 100 ms reap window. An unreaped worker prevents replacement instead
of spawning more workers. Host deadlines cannot repair an uninterruptible
kernel or a physically stuck bus.

Three consecutive I/O failures or one timeout put a channel offline. It emits
MISSING samples, waits one second and attempts at most two reconfigurations in
that run. Data-not-ready is a polling miss, not a reset trigger. Recovered
settings must match the recorded configuration. Exhausted channels stay offline
until a new run. Status messages explain failures and recovery.

The queue defaults to 64 batches (configurable 1–4096). It drops newest data on
overflow, carries known/unknown loss into the next accepted batch and retains
a final summary of losses without subsequent batches. Control messages drain
older data first and are never silently dropped. Recording retains arrival
order. A process/file failure may leave an incomplete recording.

USB chunks are at most 4096 bytes; framing has the
[contract's byte bounds](sensor-contract.md#usb-cdc-framing-and-bounds).
Partial frames expire after one second and discard through the next delimiter.
CRC, malformed Protobuf, semantic and session failures are counted and recorded.
USB permits eight open attempts per run, one second apart. Reconnect requires
identity/configuration again without erasing sequence history. USB only accepts
head identities and reserves the local Pi ID. CRC is not authentication.

Sessions retain at most four producers and 32 retired boot IDs per producer.
New boots may restart clocks/sequences. Retired boots, duplicates, backward
timestamps, contradictory known loss, stale configurations and decreasing loss
totals are rejected. Reaching a capacity requires a new recording.

## Calibration and recordings

`--calibrations` accepts a JSON list of at most 16 artifacts. Each has
`sensor_id`, `configuration_sha256`, `provenance` and `fields`. SHA-256 binds
the deterministic serialized `SensorConfiguration`, including read-back
register settings, to coefficients. Each field has explicit `scale` and `offset`
arrays (three values for vectors, one for scalars). The operation is
`SI = raw × scale + offset` in package axes; field names declare SI units.
Record the method, reference and date in `provenance`. Physical calibration
is supplied by the user, never invented by the application.

Inputs are acceleration, gyro, tilt angle, magnetic counts, IMU/tilt temperature
and DLVR 14-bit pressure counts. Finite results and sensor/field compatibility
are checked. GNSS and pressure-response temperature conversion are not
implemented. Raw values remain unchanged. The content hash becomes the
calibration ID; full artifacts are stored with recordings. Only VALID/SATURATED
samples receive calibrated values.

The streaming `.ssrec` format is `SSREC01\0`, a little-endian 32-bit JSON-header
length, header JSON, then CRC32 over magic/length/JSON. Each record contains a
little-endian `(uint8 kind, uint64 arrival_ns, uint16 length)` prefix, payload,
and CRC32 over prefix/payload. Kind 1 holds a complete delimited v1 frame;
kind 2 holds a JSON event. Metadata is bounded to 16 KiB, record payloads to
2048 bytes, and files to 64 MiB by default (up to 1 GiB). Budget exhaustion
stops acquisition with an error. There is no silent rollover or in-memory list
of a whole recording.

Replay streams records, validates CRC/order/contracts/sessions/calibration
references and computes a digest of message bytes. A final `acquisition_summary`
event marks normal completion. A complete prefix without that event is readable
but incomplete; partial/corrupt records fail. USB arrival time never replaces
remote acquisition time.

## Evidence and next gate

Tests include independent wire vectors, modeled SPI/I²C responses, ioctl buffer
and short-transfer checks, pseudo-terminal input, subprocess termination,
byte-identical CLI runs, replay, overflow and epoch recovery. They exercise
application software, not Raspberry Pi or STM32 instructions.

Next: generate/compile Nanopb C, establish C/Python interoperability, link USB-head
firmware within measured RAM/flash/stack budgets, then test enumeration and
sensors on assembled boards. Physical FPGA pin, power, clearance, thermal and
noise qualification remains in step 4.

References: [ST LSM6DSO](https://github.com/STMicroelectronics/stm32-lsm6dso),
[Murata SCL3300 rev. 4](https://www.murata.com/-/media/webrenewal/products/sensor/pdf/datasheet/datasheet_scl3300-d01.ashx),
[u-blox keys](https://github.com/u-blox/ubxlib/blob/master/gnss/api/u_gnss_cfg_val_key.h),
[MAX-M10S manual](https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf),
[Linux spidev](https://docs.kernel.org/spi/spidev.html),
[Linux I²C](https://docs.kernel.org/i2c/dev-interface.html).
