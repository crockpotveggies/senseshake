# ShakeSense repository guidance

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
The Trenz variant needs an FPGA bitstream. These software implementations and
hardware-in-the-loop qualification remain pending; do not claim emulation or
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
