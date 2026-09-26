# DAQHAT-01: one Racotech geophone

The active 85 × 56 mm DAQHAT-01 carrier replaces MAX-M10S U21, U.FL J2 and the
GNSS support capacitors with one external passive vertical geophone input.
Historical A2 and the remote USB magnetometer/infrasound board are unchanged.
All 155 Trenz GPIO assignments remain required and independently checked.

## Sensor and connector

Specify **Racotech RGI-4.5Hz, vertical, 395 Ω ±5%, 23.4 V/(m/s) ±10%,
4.5 Hz ±0.5 Hz, damping 0.70 ±10%**. Raspberry Shake documentation also calls
this its 4.5 Hz RGI-20DX; do not order another RGI-20DX frequency by name alone.
The bare element is 25.4 mm diameter × 33 mm high. Its ground-coupled external
mount must hold it vertically; HAT leveling does not establish the leveling of
a separately mounted geophone.

J90 is Phoenix Contact **1803439**, MCV 1,5/3-G-3,81. Use a matching
MC 1,5/3-ST-3,81 cable plug. Pin 1 is GEO+, pin 2 GEO−, pin 3 cable shield/GND.
The two coil wires float relative to ground and require no external power.
Use a shielded twisted pair; terminate its shield at J90, not a coil terminal.
This connector is incompatible in purpose with J83's external FPGA supply.
The render shows the PCB header, not the cable plug or external geophone.

## Circuit

- U22: ADS122C04IPWR, 24-bit delta-sigma ADC with internal PGA and 2.048 V
  reference, AIN0−AIN1, I²C address 0x40. Initial software: gain 64, normal
  330 SPS. The 24-bit word is not a claim of 24 noise-free bits.
- D90: TPD2E2U06DCKR at the connector; R90/R91 are 1 kΩ series input resistors.
  Protection is intended for handling ESD, not outdoor lightning or arbitrary
  sustained applied voltage. Qualification of the protection remains physical.
- C90: TDK C3216C0G1H104J160AA, 100 nF C0G across the differential input;
  C91/C92: 1 nF C0G to ground.
  C0G avoids using piezoelectric high-k ceramics on the measurement input.
- R92/R93: 1 MΩ bias returns to filtered mid-supply. R94/R95: 10 kΩ divider;
  C93: 10 µF. This loads the coil lightly; no additional damping shunt is fitted.
- R96: 22 Ω analog supply filter; C94/C95: 10 µF + 100 nF at AVDD;
  C96: 100 nF at DVDD. RESET is tied high. Unused analog/reference pins float,
  following TI's unused-input guidance; excitation and burnout currents are off.
- R97: 10 kΩ DRDY pullup. U42 carries its active-low output to Pi BCM4,
  formerly PPS. Existing I²C isolation and pullups are retained.

Nominal input full scale is ±32 mV. Well above the mechanical corner this is
approximately ±1.37 mm/s before loading and filtering; it is not a flat
velocity range below 4.5 Hz. The nominal electrical pole including the coil
is approximately 662 Hz. The ADC's own digital filter also shapes the response.
TI specifies typical 0.50 µV RMS ADC input noise at gain 64 / 330 SPS / 3.3 V;
this excludes the sensor, resistors, cable and board interference.

No analog hyper-damper or inverse-response compensation is implemented. Do not
claim Raspberry Shake's or AnyShake's sub-hertz system response for this board.
Preserve raw counts and characterize the assembled response before correction.

## Accelerometer axes

U11–U14 are four **three-axis** LSM6DSO IMUs, all on the front at rotation 0°.
Each measures X, Y and Z; rotating the chips is unnecessary to obtain three
axes. Four sensors provide four independent readings per axis. Raw values
retain the ST package-axis convention. No geographic orientation or automatic
averaging is implied. Hardware tests reject a rotated/flipped placement until
an explicit software axis mapping is provided. The external geophone adds a
single vertical velocity-sensitive channel.

## Acquisition and validation

Sensor ID **9** carries signed 24-bit ADC counts and the 8-bit conversion
counter. ID 6 remains reserved for legacy GNSS recordings. The active inventory
is 1–5 and 9; remote IDs remain 7 and 8. Configuration carries gain and reference.
Nominal input volts = counts × 2.048 / (64 × 2²³); velocity requires the sensor
transfer function and calibration, not simple division across all frequencies.

The Pi driver resets and reads back all registers, enables inverted-data
integrity and the conversion counter, detects duplicates/gaps/wrap ambiguity,
and marks signed endpoints saturated. There is no ADC FIFO. The current driver
polls; BCM4 is routed for future falling-edge timestamp acquisition. Poll
completion timestamps have unknown absolute uncertainty, and overwritten
conversion loss is unknown. Scheduler/IPC throughput must be measured on the
target Pi; 330 SPS conversion rate does not guarantee 330 delivered samples/s.
ADC data validity does not prove coil continuity; automatic open-coil detection
is not implemented. The current DAQHAT-01 rejects `--utc`; it contains neither GNSS nor a UTC/PPS source.

Duplicate reads do not extend the counter ambiguity window. Conversion gaps emit
missing records with unknown loss, without resetting an otherwise healthy ADC.
Actual communication faults retain bounded hardware recovery. The nominal
330-SPS setting has a 3.04296875 ms conversion period at nominal clock; do not
interpret the configured nominal period as a calibrated device timestamp.
See the [pre-fab review](pre-fab-review.md) for measured geometry, noise estimates,
2,816 analytical corner evaluations, eight added passive SPICE transients and
six-channel timing stress. The six analog path targets are now closed; optional flex-harness fit remains open.

Tests include independent pin maps, four-IMU orientation, ADC wire faults,
counter rollover, signed precision, saturation, contract clock/ID validation,
and a known 10 Hz / 100 µm/s waveform through the actual driver on a modeled bus.
SPICE checks cover 15 frequency/tolerance cases plus bias and PGA headroom.
The stimulus is a steady-state mechanical + passive RC model: no ADC digital
filter, settling, self-noise, magnetic pickup or physical mounting simulation.

Bench qualification must measure polarity/response, shorted-input and attached
sensor noise with FPGA off/on, clipping/recovery, delivery timing/loss, supply
sequence and physical cable/stack fit. Blank physical evidence never passes.

## Primary references

- [Racotech sensor datasheet](https://raspberryshake.org/wp-content/uploads/2020/05/racotech-geophone-datasheet.pdf).
- [TI ADS122C04 datasheet, SBAS751B](https://www.ti.com/lit/ds/symlink/ads122c04.pdf): PW pin map, PGA common-mode, noise table 1, registers and input filtering.
- [TI TPD2E2U06 datasheet](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf): DCK pin map and ESD characteristics.
- [Phoenix Contact 1803439](https://www.phoenixcontact.com/en-us/products/pcb-header-mcv-15-3-g-381-1803439).

## Recorded validation

The [DAQHAT-01 verification record](../hw/boards/groundlark-daqhat-01/verification.json)
records all 18 portable stages passing, 152 software tests without skips, 20
hardware regressions and 64 total SPICE cases. Native KiCad ERC/DRC and
connectivity report zero findings. Clean SES replay reproduces all 6,444 copper
items exactly. The refreshed UI passes all 10 modeled-driver checks.
See [the layout review](pre-fab-review.md) for the shortened filter/protection
paths and [assembly notes](stack-assembly.md) for component sides and via-in-pad.
