# Documentation

- **Active work:** [four-step sensor development plan](sensor-development-plan.md)
  on the Pi/DAQHAT-01/Trenz stack; Coldfoot integration is deferred.

- [Project map](project-layout.md) and [portable lab](portable-lab.md).
- [A2 design](design-a0.md), [Coldfoot module integration](coldfoot-integration.md),
  and [validation limits](validation.md).
- [DAQHAT-01 Pi-size Trenz carrier](trenz-hat.md) and [FPGA selection](fpga-options.md).
- [DAQHAT-01: internal SPI/QSPI reservation, UART, Pi JTAG and bring-up](fpga-host-link.md).
- [DAQHAT-01 hardening, expanded tests and prototype preparation](daqhat-01-link-hardening.md).
- [JLCPCB assembly package, sourcing and release holds](jlcpcb-assembly.md).
- [Supplier connector placement corrections and regression tests](assembly-placement.md).
- [Six-layer FR-4 fabrication cost reduction and quote settings](cost-reduction.md).
- [DAQHAT-01 PCB, components and assembly cost estimate](hat-cost-estimate.md).
- [Dedicated inclinometer removal: circuit, software and validation](inclinometer-removal.md).
- [IMU placement, bypass routing and remaining noise review](imu-placement-review.md).
- [Lower-cost inclinometer candidates and prototype leveling options](inclinometer-options.md).
- [Three-IMU circuit, acquisition and assembly revision](three-imu-revision.md).
- [Current DAQHAT-01 circuit, Racotech input and accelerometer axes](geophone-input.md).
- [Pi/Trenz stack, cooling, geophone plug and four straight supports](stack-assembly.md).
- [Pre-fab review: analog, timing, components/layout and stack fit](pre-fab-review.md).
- [DAQHAT-01 electrical, mechanical and acquisition closure](daqhat-01-engineering-closure.md).
- [Legacy UTC capture and pulse association](utc-timing.md) and [physical bench procedure/report](bench-procedure.md).
- [USB sensor-head interface and firmware contract](usb-sensor-head.md).
- [Hardware rebuild](build.md) and [SPICE scope](../hw/simulation/README.md).
- [Assembly rotation, exact-part and shortage regression methods](assembly-regressions.md).
- [README stack/geophone render sources](readme-render.md).
- [Sensor inventory](sensor-inventory.md) and [source references](sources.md).
- [Sensor data contract v1](sensor-contract.md) and [executable interface checks](../sw/interfaces/README.md).
- [Software responsibilities](../sw/README.md).
- [Run sensor acquisition, simulation and replay](sensor-software.md).
- [Virtual sensor controls and stimulus scenarios](stimulus-models.md).
- [Beginner sensor workbench walkthrough](sensor-workbench.md): setup, first signal, save and replay.
- [Workbench implementation and validation](workbench-development.md): model semantics and contributor tests.

The design is an engineering prototype. Read each board's validation limits
before interpreting a passing test as evidence about physical hardware.
