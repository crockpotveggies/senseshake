# ShakeSense — sensors, Raspberry Pi HATs and Coldfoot integration

**Portable tests:** run `./lab.ps1 build` once, then `./lab.ps1 test` from
PowerShell. See the [portable lab guide](docs/portable-lab.md) for profiles,
bounded scratch storage, automatic five-run retention, and cleanup previews.

| Directory | Contents |
| --- | --- |
| [hw/](hw/README.md) | Atopile circuits, KiCad boards, models, hardware checks and SPICE. |
| [sw/](sw/README.md) | Planned Pi software, remote-head firmware, FPGA integration and software tests. |
| [docs/](docs/README.md) | Design, interface contracts, validation and build instructions. |
| [environment/](docs/portable-lab.md) | Pinned Docker test environment and cleanup tooling. |

See the [project map](docs/project-layout.md) for ownership and generated-file rules.

**T1 FPGA variant:** [Pi-size 85 × 56 mm Trenz 200T carrier](docs/trenz-hat.md),
with [carrier 3D](hw/boards/shakesense-trenz-hat/3d.png) and
[three-board stack concept](hw/boards/shakesense-trenz-hat/pi-trenz-stack-concept.png).
It is an alternative to the ASIC HAT below and requires external regulated 3.3 V
FPGA power. Its FPGA bitstream port and physical qualification remain pending.

An engineering prototype with four LSM6DSO IMUs, an SCL3300 inclinometer,
MAX-M10S GNSS, a remote RM3100 XYZ magnetometer and optional DLVR differential
pressure. No geophone. The Pi acquires/preprocesses samples and submits compatible
workloads to Coldfoot through its host UART.

**A2 uses the run-1 1×1 module.** The carrier includes its supply, decoupling,
two independent 25 MHz clocks, supervised reset, digital-pad biasing and UART
power isolation. Coldfoot silicon source was not changed. This is a prototype,
**not a fabrication-qualified product**; see [validation](docs/validation.md).

The HAT is 120 × 56 mm, retaining the Pi header and four mounting-hole positions.
It extends beyond the usual Pi outline. The remote head is 70 × 45 mm.

**USB-C is only on the remote sensor head**, which plugs directly into a Pi USB
port for data and power. The HAT has no USB connector or remote cable header.
See the [USB interface and firmware contract](docs/usb-sensor-head.md).
USB firmware still needs implementation before the head can enumerate.

- [Atopile project](hw/ato.yaml), [HAT circuit](hw/elec/hat.ato), [field circuit](hw/elec/field_head.ato), [parts](hw/elec/parts.ato).
- [KiCad HAT PCB](hw/boards/shakesense-hat/shakesense-hat.kicad_pcb) and [review schematic](hw/boards/shakesense-hat/shakesense-hat.kicad_sch).
- [KiCad field PCB](hw/boards/shakesense-field-head/shakesense-field-head.kicad_pcb).
- [HAT 3D](hw/boards/shakesense-hat/3d.png), [field-head 3D](hw/boards/shakesense-field-head/3d.png), [infrasound option fitted](hw/boards/shakesense-field-head/3d-infrasound-option.png).
- [HAT BOM](hw/boards/shakesense-hat/bom.csv), [field BOM](hw/boards/shakesense-field-head/bom.csv).
- [Design](docs/design-a0.md), [Coldfoot mapping](docs/coldfoot-integration.md), [sources](docs/sources.md), [upstream sensors](docs/sensor-inventory.md).
- [Simulation scope](hw/simulation/README.md), [rebuilding](docs/build.md).
- [Artix-7 200T module shortlist and FPGA carrier requirements](docs/fpga-options.md).

Electrical changes belong in `.ato` files. `hw/layout.json` contains placement and
presentation metadata, not connections. PCB assembly reads native footprints and
nets from atopile. Review schematics are derived and checked against the board.
MPNs are explicitly selected; the automatic supplier picker is not used.

3D images are rendered by KiCad from the actual board. Standard packages use
KiCad models. Custom modules, the Pi socket and a few missing stock bodies use
simplified dimensioned envelopes, not supplier-certified STEP assemblies. The
pressure sensor is DNP in the default assembly.
