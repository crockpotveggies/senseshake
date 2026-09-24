# A2 design evidence and provenance

Reviewed 2026-09-23. These references support component selection and pin assignments; they are not evidence that the assembled design has been validated.

| Reference | Use |
|---|---|
| [AnyShake/GeoShake sensor inventory](sensor-inventory.md) | Upstream repository commits, actual sensor support, distinction between hardware and firmware |
| [wafer.space pinned run-1 module](https://github.com/wafer-space/chip-on-board-wire-bonded-pcbs/tree/90fc89d65ef5ee5d9beb64b12b9cc8fa4ced7f08/run-1) | Selected 1×1 module connector nets and mating footprint |
| [ST LSM6DSO datasheet](https://www.st.com/resource/en/datasheet/lsm6dso.pdf) | 14-pad package, primary SPI mode connections and supply bypassing |
| [Murata SCL3300-D01 datasheet](https://www.murata.com/-/media/webrenewal/products/sensor/pdf/datasheet/datasheet_scl3300-d01.ashx?la=en) | 12-pin assignment, external regulator capacitors, land pattern and SPI requirements |
| [u-blox MAX-M10S integration manual](https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf) | 18-pin assignment, 3.3 V I/O selection, I2C/PPS and RF integration |
| [PNI RM3100 breakout manual](https://www.pnisensor.com/wp-content/uploads/RM3100-Breakout-Board-User-Manual-r07.pdf) | Complete PNI 14190 module, I2C strap pins, row spacing, axis conventions and magnetic measurement behavior |
| [All Sensors DLVR DS-0300](https://www.allsensors.com/hubfs/Product-Data-Sheets/DS-0300.pdf) | Pressure range, E1BS package, digital interface and ordering-code options |
| [Raspberry Pi HAT+ specification](https://pip-assets.raspberrypi.com/categories/1215-raspberry-pi-hat/documents/RP-008281-DS-1-hat-plus-specification.pdf?disposition=inline) | Header ID bus, standby power-state requirements and EEPROM expectations |
| [KiCad Raspberry Pi HAT template](https://github.com/KiCad/kicad-templates/tree/master/Projects/raspberrypi_hat) | Reference outline and header/mounting-hole geometry; snapshot in `hw/reference/` |

Selected PDFs are cached under `hw/reference/`, together with extracted text and selected mechanical illustrations. Supplier datasheets retain their owners' copyright. Do not infer a redistribution license from their inclusion as working references.

The wafer.space source files are unmodified reference copies and retain the upstream Apache-2.0 `LICENSE`. A2 uses the selected run-1 mating footprint from its example motherboard, with documented coordinate normalization. Standard footprints come from KiCad; the license notice is retained in `hw/libraries/KICAD-COPYRIGHT`. Custom sensor footprints follow the named supplier drawings; simplified 3D envelopes are project-authored and are not supplier-certified models.

Freerouting 1.9.0 is from [the upstream release](https://github.com/freerouting/freerouting/releases/tag/v1.9.0). A2 uses atopile 0.15.9, KiCad 9.0.9/pcbnew, ngspice and Python under WSL Ubuntu 24.04. Tool environments and jars are local dependencies, not authored design files.

## A2 additional primary references

- [Run-1 module and pin convention](https://github.com/wafer-space/chip-on-board-wire-bonded-pcbs/tree/90fc89d65ef5ee5d9beb64b12b9cc8fa4ced7f08/run-1): module PCB and example motherboard footprint.
- [HCTL receptacle drawing](https://datasheet.lcsc.com/datasheet/pdf/f2ef933153da158dccaefb106ab7c3d4.pdf): 70 contacts, 0.4 mm pitch, mating heights and 300 mA/contact.
- [TI TLV1117LV](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf): sensor supply, pinout, ceramic capacitor requirements and thermal data.
- [TI SN74LVC8T245](https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf): partial-power-down GPIO isolation, direction/OE behavior.
- [TI ISO1640](https://www.ti.com/lit/ds/symlink/iso1640.pdf): I2C domain isolation and offset low-output thresholds.
- [TI TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf): fixed opposing UART directions, OE and disconnected-supply behavior.
- [TI TLV803E](https://www.ti.com/lit/ds/symlink/tlv803e.pdf): supervisor pinout, 3.0 V threshold and 200 ms delay selection.
- [Diodes AP63203](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf): buck topology, bootstrap capacitor, output capacitance and inductance range.
- [Bourns SRN6045TA](https://www.bourns.com/docs/product-datasheets/srn6045ta.pdf): selected 4.7 uH inductor, DCR, saturation/current limits and footprint.
- [Abracon ASE](https://abracon.com/Oscillators/ASEseries.pdf): 25 MHz oscillators, pinout, voltage and timing limits.
- [ST USBLC6-2](https://www.st.com/resource/en/datasheet/usblc6-2.pdf): cable-line transient steering and pinout.
- [Atopile source](https://github.com/atopile/atopile): pinned 0.15.9 atomic-part/build/solver API inspected locally. Numeric solving is explicitly invoked because this design uses manually selected parts.

The Coldfoot references are the user's existing sibling `coldfoot_soc` workspace, including uncommitted current implementation state. They have not been copied as a new chip specification or modified by this task. See [the integration note](coldfoot-integration.md) for paths and limitations.

## A2 USB sensor head

See [USB circuit and manufacturer references](usb-sensor-head.md). The former PCA9615 cable has been removed from both boards.

