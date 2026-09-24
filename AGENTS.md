# ShakeSense repository guidance

Current priority is the [sensor development plan](docs/sensor-development-plan.md)
on the Pi/T1/Trenz stack. Defer Coldfoot ASIC/runtime/RTL integration. Keep sensor
software independent of a configured FPGA; preserve the existing FPGA interfaces.
The Trenz GPIO expansion exposes 155 user I/Os on J85-J89 while retaining
sensors, existing interfaces and the 85 x 56 mm outline. Preserve the vendor
GPIO/ground fixtures and run their full module-contact audit when changing T1.
T1 uses a provisional eight-layer 1+6+1 HDI stack and a complete native SES
routing snapshot. Manufacturer DFM, GNSS RF impedance, cable/stack fit and GPIO
signal integrity still need qualification. Ethernet is not exposed.
Keep the A2 ASIC design deferred for this phase.

Keep authored inputs separate from disposable build output. Preserve unrelated
work. Hardware changes belong under `hw/`, software under `sw/`, shared design
and interface documentation under `docs/`, and portable test tooling under
`environment/`. See [the project map](docs/project-layout.md).

Electrical connectivity is authored in `hw/elec/*.ato`; placement metadata is
in `hw/layout*.json`. The routed boards and review schematics are in `hw/boards/`.
Keep custom model/library paths relative and preserve the existing 3D artifacts.
Do not invoke `bootstrap_trenz.py` or `pack_trenz.py` as validation: they overwrite
authoring inputs. Do not silently reroute or rewrite checked CAD during tests.

The accelerometer HAT uses Pi drivers/runtime software; it has no separate
microcontroller firmware. Firmware belongs to the remote USB sensor head.
The Trenz variant needs an FPGA bitstream. Pi acquisition/simulation and bounded
recovery are implemented; USB-head firmware, FPGA bitstreams and physical
qualification remain pending. Do not claim emulation or
fabrication readiness from CAD/SPICE checks.

After moving paths or changing circuits, run `python environment/check_project.py`,
`./lab.ps1 unit`, and `./lab.ps1 test` (or the `lab.sh` equivalents). Update the
affected README and design/validation documents. Use the existing hardware
checks and independent fault fixtures rather than tests that mirror the design.

Generated runs belong in ignored `.lab/`, which retains five runs. Local tool
installations and legacy caches belong in ignored `.local/`. Never commit
virtualenvs, logs, credentials, downloaded tool binaries, or Docker image archives.
Use the lab cleanup commands; do not run global Docker prune for this project.
Keep vendor attribution and the existing GPL-3.0 license.

Sensor v1 semantics live in `docs/sensor-contract.md`; field layouts are in
`sw/interfaces/proto/`. Run the portable software profile when changing either.
Preserve explicit zero/missing/unknown distinctions and raw sensor precision.
The Buf baseline is a compatibility fixture, not routine generated output.
Do not refresh it just to bypass a breaking change. Generated descriptors belong
in ignored `sw/build/` inside the lab. Follow `docs/sensor-software.md` for runtime,
loss and recovery rules. Linux drivers have modeled-bus tests; physical sensor
qualification and MCU firmware remain pending.

The local workbench is Python/NiceGUI in `sw/ui/`; its framework-independent
controller is `sw/pi/senseshake/workbench.py`. Preserve raw count/gap semantics,
per-tab sessions, bounded recording/display buffers and separation of camera
motion from stimulus controls. Keep `sw/ui/uv.lock` synchronized with its optional
project dependencies; do not add UI packages to atopile's environment. For UI
changes run its HTTP smoke check, controller tests and a browser interaction
check. The sensor software profile includes the controller tests. Update the
workbench guide and review model provenance after changing board display assets.
