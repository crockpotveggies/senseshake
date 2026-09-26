# Lower-cost inclinometer options

**Superseded population:** the dedicated inclinometer has now been removed.
See [the current revision](inclinometer-removal.md). The figures below describe
the earlier three-IMU-plus-inclinometer design/research.


Research: 2026-09-25 (America/Vancouver). USD, single IC quantities, before
shipping, tax and assembly procurement costs. This is a recommendation;
the current circuit, BOM and software still use SCL3300-D01-10.

## Recommendation

Use **ST IIS2ICLXTR** if retaining a dedicated precision leveling sensor.
It is the strongest cost/performance candidate found for a stationary HAT
installed near horizontal. For basic prototype installation leveling, consider
removing the dedicated sensor and deriving tilt from the existing three
LSM6DSO IMUs instead. That is a reduced precision requirement, not an equivalent
replacement for calibrated long-term tilt monitoring.

| Option | Single-part price | Saving against current IC | Assessment |
| --- | ---: | ---: | --- |
| Murata SCL3300-D01-10, current | $38.38 | — | Existing design and driver. [DigiKey](https://www.digikey.com/en/products/detail/murata-electronics/SCL3300-D01-10/9950617) |
| ST IIS2ICLXTR | $22.7341 | $15.6459 / 40.8% | Recommended dedicated replacement; LCSC C1857737 displayed 351 in stock. [LCSC](https://www.lcsc.com/product-detail/C1857737.html) |
| ST IIS3DHHCTR | $17.55 | $20.83 | Reject for a new design: obsolete despite remaining distributor stock. [DigiKey](https://www.digikey.com/en/products/detail/stmicroelectronics/IIS3DHHCTR/8321873), [ST lifecycle](https://www.st.com/en/mems-and-sensors/iis3dhhc.html) |
| ST LIS2DW12TR | about $1.20 | about $37.18 | Cheap general-purpose accelerometer; offers little reason to add another sensor alongside the existing IMUs. [LCSC](https://www.lcsc.com/product-detail/accelerometers_stmicroelectronics-lis2dw12tr_C189624.html) |
| Derive tilt from existing LSM6DSO IMUs | $0 additional hardware | $38.38 | Best cost reduction for basic stationary leveling; requires calibration, filtering and validity checks. |

LCSC stock is **not confirmation of JLCPCB assembly stock or final procurement
price**. JLCPCB availability for C1857737 remains unverified. DigiKey's
[IIS2ICLXTR listing](https://www.digikey.com/en/products/detail/stmicroelectronics/IIS2ICLXTR/12703503)
is $33.55 at one piece, which saves only $4.83. Confirm the sourcing route before
redesigning for cost alone. IIS3DHHC's $13.13 LCSC listing was out of stock.

## Technical fit

IIS2ICLX provides two acceleration axes, SPI/I2C, a 1.71–3.6 V supply and a
5 x 5 x 1.7 mm ceramic LGA-16 package. ST specifies typical noise of
15 micro-g/sqrt(Hz), typical offset temperature coefficient of +/-0.020 mg/C,
and characterized extrema of +/-0.075 mg/C. Those extrema are not production
guarantees. Near level, the typical temperature coefficient alone corresponds
to about 0.00115 degrees/C; this excludes other error sources. Its +/-8 mg
initial offset specification corresponds to roughly +/-0.46 degrees near level,
so zeroing after assembly matters. Noise resolution is not absolute angle
accuracy. [ST datasheet, table 2](https://www.st.com/resource/en/datasheet/iis2iclx.pdf)

Two axes support near-horizontal roll/pitch leveling with a known upright
orientation; they do not preserve the current third raw acceleration/angle
channel or provide heading. Supply/interface compatibility does not make it
pin-compatible. The substitution needs a new footprint, pin mapping, bypass
network, routing, Pi driver and sensor-specific recording semantics.

The existing LSM6DSO accelerometers measure gravity and can therefore support
stationary leveling. Their typical initial offset is +/-20 mg (about 1.15 degrees
near level) and typical temperature coefficient is +/-0.1 mg/C. Calibration can
remove initial bias, but averaging three devices does not remove shared thermal,
mounting or calibration errors. [ST LSM6DSO datasheet](https://www.st.com/resource/en/datasheet/lsm6dso.pdf)

LIS2DW12 has typical +/-20 mg offset, +/-0.2 mg/C offset drift and 90
micro-g/sqrt(Hz) high-performance noise. It is not a precision-equivalent
substitute. [ST LIS2DW12 datasheet](https://www.st.com/resource/en/datasheet/lis2dw12.pdf)

## Implementation and verification if selected

- Update atopile, the KiCad footprint/layout, decoupling and BOM, then regenerate
  native renders and the local assembly package. Preserve FPGA interfaces.
- Add device identity, configuration readback, self-test, bus-fault and recovery
  coverage. Preserve legacy SCL3300 recordings rather than relabeling its raw
  fields as readings from another IC.
- Test tilt conversion with known orientations, bias, axis signs, temperature
  changes and motion. Mark leveling invalid during significant acceleration;
  do not silently treat vibration as gravity. Retain raw seismic data.
- Establish the required angle tolerance and temperature range, then measure
  post-reflow offset, thermal drift and repeatability against a reference fixture.
  Simulation cannot establish physical angle accuracy.

At unchanged setup/fabrication allowances, the IIS2ICLX LCSC-price substitution
would move the [assembled estimate](hat-cost-estimate.md) from about $300–365 to
**$285–350**. Existing-IMU-only leveling would make it about **$262–327**.
These subtract only IC cost; neither is a fresh assembly quotation.
