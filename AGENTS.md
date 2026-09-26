# ShakeSense repository guidance

Current priority is the [sensor development plan](docs/sensor-development-plan.md)
on the Pi/T1/Trenz stack. Defer Coldfoot ASIC/runtime/RTL integration. Keep sensor
software independent of a configured FPGA; preserve the existing FPGA interfaces.
The T1-LINK revision follows docs/fpga-host-link-plan.md: six internal
QSPI signals, retained UART and four shared pins for isolated Pi-driven JTAG.
External J84-J89 and their ribbons/guide are removed. This supersedes the
155-breakout requirement. Keep the circuit, routed CAD, model and validation evidence synchronized. Preserve vendor GPIO/ground
fixtures and audit all module contacts, including deliberate no-connects, when
implementing the revision. Keep sensors and the 85 x 56 mm outline.
T1 uses a provisional eight-layer 1+6+1 HDI stack and a complete native SES
routing snapshot. Fabrication approval is owned by the user. T1-GEO removes GNSS and adds one Racotech/ADS122C04 input. Preserve its
independent pin/axis checks, GPIO riser assembly, and explicit
power envelope in docs/t1-engineering-closure.md. Geophone noise/response measurements, actual stack
fit and GPIO signal integrity still need qualification. Ethernet is not exposed.
Keep the A2 ASIC design deferred for this phase.

Keep authored inputs separate from disposable build output. Preserve unrelated
work. Hardware changes belong under `hw/`, software under `sw/`, shared design
and interface documentation under `docs/`, and portable test tooling under
`environment/`. See [the project map](docs/project-layout.md).
Generated fabrication/assembly packages in `hw/releases/` stay local and ignored.
Do not commit or push these packages unless the user explicitly requests their
publication. Keep reusable export tooling and tests tracked separately.

Electrical connectivity is authored in `hw/elec/*.ato`; placement metadata is
in `hw/layout*.json`. The routed boards and review schematics are in `hw/boards/`.
Keep custom model/library paths relative and preserve the existing 3D artifacts.
Do not invoke `bootstrap_trenz.py` or `pack_trenz.py` as validation: they overwrite
authoring inputs. Do not silently reroute or rewrite checked CAD during tests.

The accelerometer HAT uses Pi drivers/runtime software; it has no separate
microcontroller firmware. Firmware belongs to the remote USB sensor head.
The Trenz variant needs an FPGA bitstream. Pi acquisition/simulation and bounded
recovery are implemented; USB-head firmware and physical qualification remain pending. A T1-LINK
SPI echo bitstream is implemented and simulated; accelerated models and native
quad remain future work. Do not claim emulation or
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
Conversion discontinuities use `DataGap`: preserve it across worker IPC and emit
unknown-loss/missing records without treating host service jitter as broken hardware.
Do not reset the ADC just because conversions were overwritten. Preserve the
independent-clock stress tests and open findings in docs/pre-fab-review.md.
The Buf baseline is a compatibility fixture, not routine generated output.
Do not refresh it just to bypass a breaking change. Generated descriptors belong
in ignored `sw/build/` inside the lab. Follow `docs/sensor-software.md` for runtime,
loss and recovery rules. Linux drivers have modeled-bus tests; physical sensor
qualification and MCU firmware remain pending.

The optional live FIFO path pairs IMU tags by slot counter, preserves buffered
samples and rejects overrun/parity/timestamp faults. Retain unknown loss and timing
uncertainty semantics. `--utc` is rejected by current T1 live acquisition; legacy GNSS timing and PPS
evidence remain supported for recorded-data correlation. Offline correlation requires a recording-bound timing policy, never
extrapolates across invalid intervals, and preserves raw data. See docs/utc-timing.md
and docs/bench-procedure.md; missing measurements/limits must never pass a bench
report. Pi deployment and measurement tooling live under sw/pi/deploy and sw/tools.

The local workbench is Python/NiceGUI in `sw/ui/`; its framework-independent
controller is `sw/pi/senseshake/workbench.py`. Preserve raw count/gap semantics,
per-tab sessions, bounded recording/display buffers and separation of camera
motion from stimulus controls. Keep `sw/ui/uv.lock` synchronized with its optional
project dependencies; do not add UI packages to atopile's environment. For UI
changes run its HTTP smoke check, controller tests and a browser interaction
check. The sensor software profile includes the controller tests. Update the
workbench guide and review model provenance after changing board display assets.

The T1-GEO analog path targets are enforced by prefab_review.py. Preserve local
filter/protection routing and ground stitches. Four straight Pi supports replace the previous flex-cable assembly;
check the actual board in assembly_fit.py and prefab_review.py. ADC supply-pad through-vias need filled/capped
processing in the fabrication notes.
