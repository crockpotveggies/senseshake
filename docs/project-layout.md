# Project organization

| Location | Purpose |
| --- | --- |
| `hw/ato.yaml` | Three atopile build targets: ASIC HAT, USB field head, Trenz HAT. |
| `hw/elec/` | Electrical source and atomic part definitions. |
| `hw/layout/`, `hw/layout*.json` | Compiled connectivity and mechanical placement inputs. |
| `hw/boards/` | Routed KiCad projects, review schematics, BOMs, 3D previews and recorded validation. |
| `hw/libraries/`, `hw/models/` | Shared KiCad symbols/footprints and local 3D models. |
| `hw/tools/`, `hw/tests/`, `hw/simulation/` | CAD tooling, electrical fault fixture, bounded SPICE models and recorded results. |
| `hw/reference/`, `hw/vendor/` | Component references and upstream board material. |
| `sw/interfaces/` | Versioned Protobuf, compatibility baseline, reference validation/framing. |
| `sw/tools/` | Offline schema and software check entrypoint. |
| `sw/pi/` | Planned Pi drivers/configuration, acquisition, calibration and accelerator runtime. |
| `sw/field-head/` | Planned USB microcontroller firmware. |
| `sw/fpga/` | Planned Trenz bitstream integration and board constraints. |
| `sw/tests/` | Executable contract/framing fixtures; later acquisition integration tests. |
| `sw/ui/` | Python/NiceGUI workbench, locked optional dependencies and display assets. |
| `docs/` | Design decisions, interface contracts, validation limits, vendor references and build instructions. |
| `environment/` | Pinned portable toolchain, launcher implementation and safeguard tests. |
| `.lab/` | Ignored disposable reports, bounded by retention. |
| `.local/` | Ignored local dependencies and preserved legacy caches. |

Run the root `lab.ps1` / `lab.sh` commands from any working directory. Low-level
commands documented elsewhere assume the repository root as the working directory.
The atopile project itself is now `hw/`, so direct builds must target that directory.

The initial uploaded checkpoint preserves the old layout in Git history. The
organization change moves files and adjusts tooling/documentation/model paths;
it does not redesign circuits or routing. Old virtual environments and caches
were preserved locally under `.local/legacy/`, with bootstrap downloads under
`.local/bootstrap/`. Recreate tools from the portable environment instead of
relying on those migrated virtual environments.

Keep normative interface documentation in its existing `docs/` location. Software
READMEs link to those contracts rather than creating competing specifications.
Software includes tested contracts, Pi acquisition/simulation, modeled Linux
drivers, calibration and bounded recording/replay. MCU firmware, physical driver
qualification and a Trenz bitstream remain pending. Generated descriptors stay in ignored `sw/build/`
inside the disposable lab workspace.

## Reorganization validation

The relocated project passed all 12 portable hardware steps on 2026-09-24 UTC
(`20260924T070004Z-a6e09804`), including fresh builds, numeric constraint checks,
zero native KiCad ERC/DRC findings, connectivity checks, and all 37 SPICE cases.
The nine applicable Linux cleanup tests passed; the Windows-only junction test
was skipped in that container.

Electrical `.ato` files and placement metadata were compared with the initial
Git checkpoint and are unchanged. All six routed/concept PCB files differ only
in their relative custom-model references. The updated structure check validates
authored Markdown links, Python syntax, and relative local CAD dependencies;
upstream README snapshots retain their upstream-relative links verbatim.
