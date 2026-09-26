# AnyShake and GeoShake sensor inventory

Reviewed: **2026-09-23**. Purpose: identify supported sensors before selecting parts for a Raspberry Pi HAT with future Coldfoot processing.

“Supported” below means evidence in a published bill of materials (BOM), a selected firmware path, or an explicit driver. It does not mean that a sensor has been tested on Groundlark, that the reference firmware runs on Raspberry Pi, or that related parts are interchangeable. Current default branches were inspected; this is not an exhaustive history of every released board.

## Motion sensors

| Sensor | Measurement | AnyShake evidence | GeoShake evidence | Reference interface and configuration |
|---|---|---|---|---|
| **LGT-4.5C** | Single-axis geophone; ground velocity | Explorer BOM labels one input connector with this part; assembly guide identifies the vertical channel. Explorer documents 4.5 Hz geophones. [A1, A2, A9] | No geophone acquisition found in the reviewed DAQHAT-01/DIY implementations. | Analog signal through conditioning and an ADS1262 ADC. One vertical sensor in the three-geophone configuration. |
| **LGT-4.5C/H** | Single-axis horizontal geophone; ground velocity | Explorer BOM labels two input connectors with this part; assembly guide identifies two horizontal channels. [A2, A9] | No corresponding support found. | Two analog channels for north/east motion, plus the vertical channel above. Connector labels identify intended sensors, not a complete geophone purchasing specification. |
| **ST LSM6DSR** | Three-axis acceleration; IMU also contains a gyroscope | Current Explorer BOM U16 and default E-C111G build at hardware revision 20250804. [A2–A4] | Not explicitly identified by the reviewed GeoShake driver; do not infer support from the family name. | Explorer uses **I²C**, ±2 g, 416 Hz internal accelerometer ODR; acquisition reads 16-bit axis data. [A3, A5, A6] |
| **ST LSM6DS3** | Three-axis acceleration; IMU also contains a gyroscope | E-C111G firmware path for revisions **before 20250804**. [A3] | Current DIY driver explicitly supports it; older ESP32/ESP8266 variants also use it. [G2–G4] | Explorer: I²C, ±2 g, 416 Hz ODR. GeoShake DIY: SPI, ±2 g, nominal 104 Hz, 16-bit axes. Legacy GeoShake includes SPI and I²C variants. |
| **TDK InvenSense ICM-42688-P** | Three-axis acceleration plus three-axis angular velocity capability | Explorer E-C121G firmware uses the `icm42688` driver; the separate breakout BOM identifies the **-P** part. The breakout targets Arduino/Raspberry Pi. [A3, A7, B1, B2] | No explicit support found. | Explorer: I²C, ±2 g, 500 Hz accelerometer ODR, 16-bit acquisition; gyro explicitly off. Breakout exposes SPI/I²C. |
| **ST LSM6DSO** | Three-axis acceleration; IMU also contains a gyroscope | Not in the reviewed Explorer selection paths. | **Four devices in DAQHAT-01 Rev-C**; also explicitly accepted by the DIY driver. [G1–G3] | Shared SPI, individual chip selects; nominal 104 Hz, ±2 g, 16-bit axes. DAQHAT-01 disables gyroscopes and averages acceleration across sensors. |
| **ST LSM6DS3TR-C** | Three-axis acceleration; IMU also contains a gyroscope | Not explicitly selected by the reviewed Explorer firmware. | Current DIY guide names it and the driver accepts its identity (`0x6A`). This is DIY driver support, not the DAQHAT-01 BOM. [G2, G3] | DIY SPI path, ±2 g, nominal 104 Hz, 16-bit axes. |
| **Murata SCL3300-D01** | Three-axis acceleration and inclination capability | Separate **evaluation board**, with BOM and firmware; not an Explorer production sensor selection. [C1–C3] | No explicit support found. | SPI. EVB firmware polls acceleration at a configured 250 samples/s; this is a software acquisition rate, not a claim of 250 Hz sensor bandwidth. |

The AnyShake IMUs are alternatives for different builds, not three accelerometers installed together. Its six seismic channels mean **three geophone channels plus three acceleration axes**, not acceleration plus gyroscope. Explorer documents output rates of 50/100/200/250 samples/s; those must be distinguished from each IMU's internal ODR. [A1, A3, A4]

GeoShake's supported part list is narrower than “all LSM6 devices”: the reviewed DIY driver explicitly recognizes LSM6DS3, LSM6DS3TR-C and LSM6DSO. Identity recognition alone does not establish compatibility with every device sharing an ID. [G3]

## Auxiliary measurements and timing

| Function | Evidence | Implication for the HAT |
|---|---|---|
| **Temperature** | Explorer reads temperature registers from its selected LSM6DSR, LSM6DS3 or ICM-42688. [A5] | This is IMU die temperature, not evidence of a separate calibrated ambient temperature sensor. Retain it as diagnostic metadata; an ambient sensor would be a new choice. |
| **Inclination / leveling** | Explorer advertises a leveling feature but its reviewed BOM does not identify a separate inclinometer. The SCL3300 EVB is a distinct project. [A1, A2, C1] | Do not add SCL3300 to the Explorer BOM based on its leveling description. A dedicated inclinometer remains optional. |
| **GNSS time and position** | Explorer has UART GNSS handling and a PPS interrupt. Its BOM names **u-blox NEO-M8M**, while default firmware selects **Allystar TAU1114**. [A2, A4, A8] | Treat the BOM and firmware selection as different evidence. Choose a receiver, electrical interface, antenna and PPS timing contract explicitly. |

Explorer's GNSS implementation contains setup branches for these **10 named receiver models**, plus a generic path: [A8]

- **Quectel:** LC260Z, LC261Z, LC760Z, LC761Z, L76K.
- **Zhongkewei:** ATGM332D, ATGM336H.
- **Allystar:** TAU812S, TAU1113, TAU1114.

**L26K is declared in the header but lacks a matching implementation branch** in the reviewed `model.c`; it is not counted as implemented support. NEO-M8M has BOM evidence, but no dedicated named setup branch in that file. These findings do not establish pin or footprint compatibility between modules.

No dedicated pressure, humidity, microphone/infrasound or magnetometer support was identified in the acquisition paths reviewed here. Gyroscope hardware capability is not equivalent to a supported seismic output channel.

## Acquisition components that are not sensors

AnyShake's **ADS1262IPWR** is the geophone ADC; its **ADA4528-2ARMZ** devices belong to the analog conditioning circuitry. They matter to a geophone HAT but should not be counted as transducers. [A2]

The reviewed Explorer reader switches a single ADC between three differential input pairs. Consequently, its multi-channel operation is not evidence of simultaneous analog conversion on all three axes. A new design needs an explicit channel-skew requirement. “32-bit ADC” also describes the conversion format, not demonstrated 32-bit usable precision. [A5]

## Initial HAT direction — proposals, not selected requirements

1. **Start with one three-axis MEMS accelerometer.** LSM6DSO is a useful first evaluation candidate because GeoShake supplies both a deployed four-sensor reference and a small explicit SPI driver. Consider optional additional sensor sites only if measured noise justifies an array. [G1, G3]
2. **Keep a geophone acquisition option.** AnyShake supplies a concrete reference for one vertical plus two horizontal 4.5 Hz geophones. This option needs external sensor connectors, analog conditioning, an ADC and suitable mechanical mounting. Validate a specific geophone's sensitivity, coil resistance, damping and response before copying gain/filter values. [A1, A2, A9]
3. **Evaluate LSM6DSR or ICM-42688-P as alternatives**, and SCL3300-D01 if inclination or low-frequency acceleration becomes a requirement. The inventory alone does not establish which has the best noise, power or cost for our target bandwidth.
4. **Consider an optional GNSS/PPS connection** if correlation between stations is required. Sensor sample timing and timestamp capture need a design of their own.
5. **Define Coldfoot access after the acquisition requirements.** Preserve raw samples and their precision, sensor identity, axis mapping, timestamps and status through the proposed processing path. Coldfoot's bus, package pins, voltage domains and host protocol remain unresolved here; this research establishes no direct sensor-to-Coldfoot compatibility.

Before schematic capture, compare candidate datasheets, availability, noise over the required passband, power, sample timing, filtering and mounting. The later bench plan should measure sample loss, channel skew, stationary noise, clipping, temperature drift and calibrated response. No electrical or performance tests were run for this inventory.

## Source record

Repository snapshots inspected:

| Repository | Branch | Commit |
|---|---|---|
| anyshake/explorer | master | `0404bea927f25ca75e0c832fd0a33bcd1ed13b22` |
| anyshake/icm-42688-breakout | master | `b4f35e0759763c8e6bcaafed687799e2f0148c36` |
| anyshake/scl3300-d01-evb | master | `fa6fea1654e929ead7e15559e8f339501428d662` |
| GeoShake/geoshake | main | `9afdcf932202241b8bef12eeca40c1e8e9b594c7` |

- **A1:** [Explorer overview and output specifications](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/README.md).
- **A2:** [Explorer BOM](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/hw/boards/Explorer.csv).
- **A3:** [Explorer sensor selection and initialization](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/peripheral.c).
- **A4:** [Explorer default build configuration](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/platformio.ini).
- **A5:** [Explorer acceleration, temperature and ADC acquisition](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/reader.c).
- **A6:** [LSM6DSR I²C implementation](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/lsm6dsr/utils.c); [LSM6DS3 I²C implementation](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/lsm6ds3/utils.c).
- **A7:** [ICM-42688 I²C implementation](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/icm42688/utils.c).
- **A8:** [GNSS model declarations](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Inc/gnss/model.h), [implemented setup branches](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/gnss/model.c), [GNSS/PPS acquisition](https://github.com/anyshake/explorer/blob/0404bea927f25ca75e0c832fd0a33bcd1ed13b22/firmware/User/Src/main.c).
- **A9:** [AnyShake assembly guide: vertical/horizontal geophone mounting](https://anyshake.org/docs/anyshake-explorer/E-C111G/assembly-guide/) (live documentation).
- **B1:** [ICM-42688 breakout overview](https://github.com/anyshake/icm-42688-breakout/blob/b4f35e0759763c8e6bcaafed687799e2f0148c36/README.md).
- **B2:** [ICM-42688-P breakout BOM](https://github.com/anyshake/icm-42688-breakout/blob/b4f35e0759763c8e6bcaafed687799e2f0148c36/hw/boards/BOM.csv).
- **C1:** [SCL3300 EVB overview](https://github.com/anyshake/scl3300-d01-evb/blob/fa6fea1654e929ead7e15559e8f339501428d662/README.md) and [BOM](https://github.com/anyshake/scl3300-d01-evb/blob/fa6fea1654e929ead7e15559e8f339501428d662/haradware/scl3300-evb.csv).
- **C2:** [SCL3300 EVB acquisition](https://github.com/anyshake/scl3300-d01-evb/blob/fa6fea1654e929ead7e15559e8f339501428d662/firmware/User/Src/main.c) and [SPI driver](https://github.com/anyshake/scl3300-d01-evb/blob/fa6fea1654e929ead7e15559e8f339501428d662/firmware/User/Src/scl3300/utils.c).
- **C3:** [Murata description of SCL3300-D01 inclination and SPI capability](https://www.murata.com/news/sensor/inclinometer/2018/1114).
- **G1:** [GeoShake DAQHAT-01 Rev-C sensor configuration and interface](https://github.com/GeoShake/geoshake/blob/9afdcf932202241b8bef12eeca40c1e8e9b594c7/firmware/daqhat-01-revc/README.md).
- **G2:** [GeoShake DIY supported breakout parts](https://github.com/GeoShake/geoshake/blob/9afdcf932202241b8bef12eeca40c1e8e9b594c7/diy/README.md).
- **G3:** [GeoShake DIY driver: explicit identities, SPI setup and raw format](https://github.com/GeoShake/geoshake/blob/9afdcf932202241b8bef12eeca40c1e8e9b594c7/diy/firmware/geoshake_diy/lsm6_spi.h).
- **G4:** [GeoShake legacy variants and maintenance status](https://github.com/GeoShake/geoshake/blob/9afdcf932202241b8bef12eeca40c1e8e9b594c7/firmware/legacy/README.md).

GeoShake explicitly distinguishes its open firmware/enclosure from its **unpublished proprietary PCB and schematics** in the [project overview](https://github.com/GeoShake/geoshake/blob/9afdcf932202241b8bef12eeca40c1e8e9b594c7/README.md). AnyShake publishes KiCad hardware sources. This document records component facts and design observations; it imports no upstream implementation.
