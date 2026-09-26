# Portable test environment

**DAQHAT-01 revision:** GNSS is removed; one external Racotech vertical geophone
uses an ADS122C04 input. See [current circuit, acquisition and validation](geophone-input.md).
GNSS/PPS/RF details below describe the preceding revision or legacy recordings.
The current physical bench template is version 3, with geophone and internal
FPGA programming/transport measurements. See the [bench procedure](bench-procedure.md).

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
.\lab.ps1 test -Profile software # Sensor application, contracts and recovery
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
| `full` (default) | Fresh atopile builds for A2, USB field head, and DAQHAT-01; numeric constraint solves; unsafe 5 V IMU rejection; independent hardware regressions; native KiCad ERC/DRC/connectivity; DAQHAT-01 power/clearance and pre-fab review; clean routing replay; SPICE; the software profile (22 stages). |
| `quick` | Same GPIO/component fault, circuit/PCB consistency, routing replay, SPICE and software checks using saved compiled layouts. Does **not** prove `.ato` changes were rebuilt. |
| `spice` | 27 A2/field, 14 Trenz, 15 geophone response, 8 geophone transient and 38 host-link switch/RC cases, including expected fault detection. |
| `software` | RTL and Python-to-RTL co-simulation; recorded Vivado evidence/hash gate; Buf format/lint/build and compatibility; acquisition/replay, modeled driver and Linux TTY/worker fault tests; retained eight-sensor demo. No physical hardware execution. |

The runner calls the existing project entrypoints. Routing reconstruction stays
in a temporary tree; it does not rewrite source CAD, render images, or release fabrication files. A full test
compares freshly compiled connectivity with the saved routed boards and should
fail if they disagree.

These are bounded electrical models, RTL simulations and CAD checks. They do not
emulate sensor silicon, USB enumeration, a booted Raspberry Pi or Coldfoot execution.
They do not establish regulator stability, extracted signal/power integrity,
thermal performance, physical mating, or fabrication readiness.

## Where files go

```text
groundlark/
  hw/                circuits, routed CAD, models and hardware checks
  sw/                Pi software, USB firmware and FPGA integration scopes
  docs/              shared design and interface documentation
  environment/       small runner, Dockerfile, dependency lock and safety tests
  lab.ps1 / lab.sh   entrypoints
  .local/            ignored local tools and preserved legacy caches
  .lab/
    .groundlark-lab   ownership marker
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
project's image, use `docker image rm groundlark/lab:1` after tests have stopped.
Do not use global `docker system prune` or `docker volume prune` as project
cleanup: other projects, including Coldfoot, share this Docker installation.

## Moving or updating it

Clone the Git repository, or copy the authored project and environment directory
(excluding `.lab/` and `.local/`) to another machine,
then run `build`. No absolute `C:` or `P:` paths are encoded in the runner. The
image pins the KiCad base and uv installer by digest; atopile 0.15.9 and its
transitive Python dependencies are pinned with package hashes. Python is 3.14.7.
Device-tree compiler 1.6.1-4+b1 supplies real overlay compile/merge tests.
The KiCad base supplies KiCad 9.0.9 and ngspice 39; previous WSL validation used
ngspice 42. The reports explicitly record this difference.

For an offline transfer, optionally save a **single image archive**:

```powershell
docker save -o groundlark-lab-image.tar groundlark/lab:1
# On the receiving machine:
docker load -i groundlark-lab-image.tar
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
fully usable. The software/full/quick profiles validate the sensor application,
contracts, framing, recording/replay and bounded recovery. MCU firmware and
physical device behavior remain outside these checks.
Buf 1.73.0 is downloaded only during image build and SHA-256 checked; Protobuf
5.29.6 reuses the existing Python lock. Runtime tests remain offline.

## Recorded validation

The UTC/bench update passed the software profile in
`20260925T040959Z-8ae6ce16`: **140 tests** without skips, including 15 UTC/timed-GNSS
tests and four bench-report tests, plus existing contract compatibility and demos.
Ten containment tests passed; the Windows junction case was skipped inside Linux.
CAD is unchanged from the DAQHAT-01 engineering checkpoint below. See
[UTC timing](utc-timing.md) and [physical bench procedure](bench-procedure.md).

The DAQHAT-01 engineering update passed all **15 stages** in
`20260925T033256Z-8be95398`: fresh atopile builds, native ERC/DRC/connectivity,
14 hardware regressions, RF/power/clearance checks, **41 bounded SPICE cases**,
and **121 software tests** without skips. The software suite includes real
device-tree compile/merge and modeled FIFO integration. Ten lab containment
tests passed; the Windows junction case was skipped inside Linux. Browser
verification passed **10/10 modeled HAT signal checks**, 1,040 samples.
Current toolchain and board hashes are retained in the
[verification record](../hw/boards/groundlark-daqhat-01/verification.json).
The records below describe earlier checkpoints, not the current test count.

The stimulus-model update passed the software profile as
`20260924T200116Z-fcdb78d1`: **80 tests**, Buf compatibility and the CLI demo/replay.
The retained two-second scenario has 480 samples, 30 MISSING, 52 SATURATED and
three timed control events. The test suite separately regenerates an exported
scenario byte-for-byte. No CAD or environment changes were needed for this update;
the preceding full hardware/software checkpoint is recorded below.

The full profile passed all **14 steps** on 2026-09-24 in **80.93 seconds**,
run `20260924T185342Z-725219f6`. It includes fresh circuit builds/constraint
solves, the negative voltage fixture, nine GPIO tests, native ERC/DRC/connectivity,
37 bounded SPICE cases and **61 software tests**, plus Buf compatibility and
deliberate breaking-change rejection. No software tests were skipped in Linux.

Reports occupy 2.1 MiB and follow five-run retention. The software-only profile
also passed as `20260924T185330Z-752713b5`. Both execute and replay the eight-sensor
demo: 480 samples, 30 MISSING and two SATURATED; repeated runs produce identical
bytes. This is deterministic application testing, not sensor/MCU emulation.
Ten cleanup/staging safeguards passed in Linux; the Windows-only junction test
was skipped. Staging includes Pi sources/profiles and excludes generated output.

Image ID: `sha256:cea708e4071d62e115358fa08176554f81d4e61c7503e6469e6fcd0879c2c3a3`. Toolchain: KiCad 9.0.9,
atopile 0.15.9, Buf 1.73.0 and Protobuf 5.29.6.
The source CAD was unchanged. The earlier DAQHAT-01 hardware checkpoint and its copper
replay evidence remain in the [hardware verification record](../hw/boards/groundlark-daqhat-01/verification.json).

## Next simulation layers

Add these as separate profiles using the same scratch/report rules:

1. **USB-head firmware:** compile the C codec and sensor scheduling against
   fake buses, check C/Python interoperability and link the actual USB stack
   against measured RAM/flash/stack budgets. Pi software scheduling, calibration,
   replay and fault injection are already in the software profile.
2. **Pi deployment:** qualify the five-select device tree and actual Linux
   buses on the selected Pi. The host application and pseudo-terminal transport
   are tested without hardware. Keep ARM compatibility checks
   separate from emulating physical Pi GPIO. USB descriptor/enumeration tests
   need a Linux virtual USB harness or a real head; normal containers do not
   emulate a USB microcontroller.
3. **FPGA connectivity:** add a narrowly scoped test bitstream for the already
   audited carrier pin map. Coldfoot and accelerator RTL work remains deferred.
4. **Bench gates:** power sequencing/current limits, USB electrical behavior,
   physical fit, thermal drift/noise and hardware-in-the-loop remain required
   before fabrication confidence can be claimed.

Do not add a full VM, SDK, FPGA tool installation, waveform dump, or dependency
checkout to the source tree just to prepare for a future profile. Add a profile
when there is executable code and an explicit acceptance test for it.

References: [official KiCad container images](https://www.kicad.org/download/docker/),
[Docker runtime options](https://docs.docker.com/reference/cli/docker/container/run).

## Current DAQHAT-01 validation

Run `20260925T214440Z-e4e115ce` passes all **22 portable stages**: three Atopile
builds/solves, invalid-voltage rejection, **33 hardware regressions**, native
ERC/DRC/connectivity, clean routing replay, **102 SPICE cases**, RTL/host
co-simulation, the implementation-evidence gate and **181 software tests without
skips**. Replay reproduces all **7,522 copper objects**, including **11 microvias**,
with zero DRC/unrouted findings. Sensor acquisition passes all 10 modeled signal
checks over 3,672 samples. The UI HTTP/model check also passes.

The Python client talks to real simulated RTL pins across all 193 payload sizes,
sequence wrap, 20 clock phases and 491 fault/reset cases. Independent fixtures
check all 32 link components and all 260 module contacts. See the
[verification record](../hw/boards/groundlark-daqhat-01/verification.json) and
[hardening review](daqhat-01-link-hardening.md).

Rebuild the image after this revision: Icarus 11.0 and hash-pinned sexpdata 1.0.2
for the native KiCad Python interpreter are required. Vivado implementation is
separate, using `sw/fpga/build.tcl` from ignored `.local/` storage. The portable
suite checks the recorded report/source hashes; it does not synthesize in Docker.
Current 50 MHz setup/hold slack is +10.143 / +0.109 ns.

Passing simulations and CAD envelopes do not replace physical power, fit, noise,
thermal or signal measurements. Pi/Trenz programming and switching still need
hardware bring-up. The version-3 [bench procedure](bench-procedure.md) requires
internal-link measurements and rejects old or incomplete report inventories.
