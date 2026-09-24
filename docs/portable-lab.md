# Portable test environment

The project now has one disposable Docker test environment. Keep authored files
in their existing locations and use the root `lab.ps1` or `lab.sh` launcher for
validation. Existing local virtual environments and historical reports are not
required by this runner and are not removed by cleanup.

## Start here

Prerequisites: Docker with Linux containers, Python 3.12 or newer, and enough
Docker memory for an 8 GiB container. Both are already available on the current
Windows machine. The toolchain is Linux/amd64; other host architectures require
Docker's amd64 emulation and have not been verified.

From the project folder in PowerShell:

```powershell
.\lab.ps1 build                 # Once; needs Internet
.\lab.ps1 doctor                # Show exact installed tool versions
.\lab.ps1 test                  # Full circuit + PCB + SPICE validation
.\lab.ps1 test -Profile quick   # Saved compiled circuit/PCB + SPICE checks
.\lab.ps1 test -Profile spice   # Only bounded SPICE cases
.\lab.ps1 unit                  # Cleanup/staging safeguards
```

On Linux/macOS, use `sh ./lab.sh build`, `sh ./lab.sh test`, and
`sh ./lab.sh test --profile quick`. Alternatively, run
`python environment/host.py test` on Windows or `python3 environment/host.py test`
elsewhere. Paths are relative to the launcher, not the current working directory.
No global Python packages or project virtual environments are installed.

Windows Docker Desktop could not bind-mount this machine's `P:` drive. The
launcher therefore sends an allowlisted source snapshot through Docker's API,
runs against that copy, and copies reports back. This also works without Docker
drive-sharing configuration. No host directory is mounted into the container.

## What each profile proves

| Profile | Checks |
| --- | --- |
| `full` (default) | Fresh atopile builds for A2, USB field head, and T1; explicit numeric constraint solve for each; rejection of the deliberately unsafe 5 V IMU fixture; circuit invariants; native KiCad ERC/DRC and connectivity checks for all three boards; 37 bounded SPICE cases. |
| `quick` | Same circuit/PCB consistency and SPICE checks using saved compiled layouts. Does **not** prove `.ato` changes were rebuilt. |
| `spice` | 27 A2/field support-circuit cases and 10 Trenz support-circuit cases, including expected fault detection. |

The runner calls the existing project entrypoints. It does not reroute boards,
rewrite source CAD, render images, or release fabrication files. A full test
compares freshly compiled connectivity with the saved routed boards and should
fail if they disagree.

These are bounded electrical models and CAD checks. They do not simulate sensor
silicon, USB enumeration, a Raspberry Pi, a Trenz bitstream, or Coldfoot execution.
They do not establish regulator stability, extracted signal/power integrity,
thermal performance, physical mating, or fabrication readiness.

## Where files go

```text
senseshake/
  hw/                circuits, routed CAD, models and hardware checks
  sw/                Pi software, USB firmware and FPGA integration scopes
  docs/              shared design and interface documentation
  environment/       small runner, Dockerfile, dependency lock and safety tests
  lab.ps1 / lab.sh   entrypoints
  .local/            ignored local tools and preserved legacy caches
  .lab/
    .senseshake-lab   ownership marker
    .lock            prevents simultaneous run/cleanup
    runs/<run-id>/   status, input hashes, tool versions, logs, result files
```

The source snapshot, build tree, package caches and tool temporary files live
inside memory-backed container filesystems and disappear when the container
exits. The test process runs without root privileges. Input files are owned by
root and read-only to that process; the container root filesystem is read-only.
There are no persistent Docker volumes, hardware passthroughs, host-network
access, or mounted Docker sockets.

Containment limits:

- Keep the **five newest runs**, including failures. Before a new run, older
  marked runs are removed automatically. Save evidence you need to keep outside
  `.lab` before the next run; do not treat `.lab` as an archive.
- Scratch workspace: 2 GiB; tool temporary files: 512 MiB; source snapshot:
  512 MiB; reports inside a run: 256 MiB. Individual logs/files: 32 MiB.
- Refuse to start if retained host data exceeds 1 GiB after retention cleanup.
  This is a start check, not a host filesystem quota.
- Container: 8 GiB RAM, four CPUs, 256 processes. Each test step times out after
  ten minutes. A container abandoned by a terminated launcher expires after one
  hour. Normal success/failure stops and removes it immediately.
- Test runs use no network. Dependencies are downloaded only during image build.

Each report identifies the exact image ID and tool versions, hashes the inputs,
records step outcomes, and includes generated SPICE decks and logs. The launcher
checks that the host inputs did not change during the run. Reports are copied
back after execution; forcibly terminating Docker can lose that run's in-memory
details. Its host status marker remains for diagnosis and later cleanup.

## Cleanup

```powershell
.\lab.ps1 clean                 # Preview old runs beyond the newest five
.\lab.ps1 clean -Apply          # Remove those old runs
.\lab.ps1 clean -All            # Preview removing every run
.\lab.ps1 clean -All -Apply     # Remove all disposable test evidence
```

Equivalent shell flags are `clean --apply` and `clean --all --apply`. Cleanup
works without Docker. It requires the lab ownership marker, validates every run
marker and final absolute path, refuses symlinks/junctions and unknown folders,
and acquires the same lock used by tests. It only removes recognized run folders.
It leaves authored files, CAD, existing virtual environments, and the old `C:`
project copy alone. An unexpected folder causes cleanup to stop for inspection.

The reusable Docker image and Docker build cache live in Docker Desktop's disk,
outside `.lab`. The installed image reports about 2.92 GB, including 2.25 GB
shared with its KiCad base. Normal test runs do not rebuild or grow this image.
Use `docker system df` to inspect storage. To remove this
project's image, use `docker image rm senseshake/lab:1` after tests have stopped.
Do not use global `docker system prune` or `docker volume prune` as project
cleanup: other projects, including Coldfoot, share this Docker installation.

## Moving or updating it

Clone the Git repository, or copy the authored project and environment directory
(excluding `.lab/` and `.local/`) to another machine,
then run `build`. No absolute `C:` or `P:` paths are encoded in the runner. The
image pins the KiCad base and uv installer by digest; atopile 0.15.9 and its
transitive Python dependencies are pinned with package hashes. Python is 3.14.7.
The KiCad base supplies KiCad 9.0.9 and ngspice 39; previous WSL validation used
ngspice 42. The reports explicitly record this difference.

For an offline transfer, optionally save a **single image archive**:

```powershell
docker save -o senseshake-lab-image.tar senseshake/lab:1
# On the receiving machine:
docker load -i senseshake-lab-image.tar
```

Keep that archive on transfer storage, not in the source repository or `.lab`.
Source plus an exported image gives a stronger toolchain snapshot than rebuilding
from online registries. Container runtime/kernel versions still vary by host.
The checked-in `requirements.lock` is consumed directly; the old project venvs
are never copied. `installed-constraints.txt` records the versions used when
creating that lock. Update pins deliberately and rerun the complete suite.

An [inactive GitHub Actions template](../environment/ci/README.md) can run the
structure checks, cleanup tests, and full hardware profile on pushes and pull
requests, with report retention of seven days. It has not been installed because
the current GitHub login lacks workflow-management scope. The local suite is
fully usable. Neither the local suite nor this template validates the planned
software under `sw/`.

## Recorded validation

The full profile passed on this Windows/Docker Desktop machine in 74.69 seconds
(2026-09-23 Pacific / 2026-09-24 UTC). Run ID:
`20260924T064109Z-31a9e9c0`. It completed all 12 steps, including all three fresh
builds and constraint solves, the negative voltage fixture, native ERC/DRC,
connectivity checks, and 37 SPICE cases. Reports were successfully retrieved to
`P:\Personal\senseshake\.lab\runs\20260924T064109Z-31a9e9c0`, using 1.9 MiB.
The container then stopped and was removed. This report is subject to retention.

Nine applicable safeguard tests passed in Linux. Eight passed natively on
Windows, including junction rejection and concurrent lock exclusion; two real
symlink tests were skipped there because the Windows account cannot create
symlinks, and both passed in Linux. Together these exercise all ten tests.
An actual cleanup attempt during the full run also refused to proceed, and a
subsequent `clean -All` preview listed only the two marked disposable runs.

Image ID:
`sha256:a9be2b44b81bc1f9fe131df63a363cc9f28f99f75138432aadd483dd8e3ff804`.
No authored circuit or PCB was changed by this validation.

## Next simulation layers

Add these as separate profiles using the same scratch/report rules:

1. **Portable firmware logic:** compile the real sensor scheduling, framing,
   calibration, and recovery code against fake I2C/SPI/UART/clock adapters. Replay
   fixed-seed recordings and inject missing devices, short reads, bad frames,
   disconnects, time jumps, saturation and buffer overflow. Compare against
   independently specified expected outputs.
2. **Pi host integration:** run the actual Linux host process against those
   adapters and a simulated remote-head transport. Keep ARM compatibility checks
   separate from emulating physical Pi GPIO. USB descriptor/enumeration tests
   need a Linux virtual USB harness or a real head; normal containers do not
   emulate a USB microcontroller.
3. **Coldfoot/FPGA:** invoke the existing RTL test flow from the Coldfoot repo
   against its current runtime contract. Mount/copy only explicitly selected
   inputs, pin simulator versions in a separate image, and retain waveforms only
   on failure with a size limit. The Trenz pin/clock/bitstream port is still needed.
4. **Bench gates:** power sequencing/current limits, USB electrical behavior,
   physical fit, thermal drift/noise and hardware-in-the-loop remain required
   before fabrication confidence can be claimed.

Do not add a full VM, SDK, FPGA tool installation, waveform dump, or dependency
checkout to the source tree just to prepare for a future profile. Add a profile
when there is executable code and an explicit acceptance test for it.

References: [official KiCad container images](https://www.kicad.org/download/docker/),
[Docker runtime options](https://docs.docker.com/reference/cli/docker/container/run).
