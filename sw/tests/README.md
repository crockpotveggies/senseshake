# Software validation

The runnable contract suite (`test_contract.py`) uses an independently specified
binary producer fixture and covers semantics, corruption and bounded framing.
Run `./lab.ps1 test -Profile software` from the repository root.

The acquisition, driver and Linux I/O suites run the actual application against
independent expectations: recordings, bus errors, time jumps, malformed frames,
queue limits, disconnects, a real pseudo-terminal and a hung subprocess. The
portable runner retains a bounded demo recording and replay summary.
See [the runtime guide](../../docs/sensor-software.md) for limits and commands.
`test_stimulus.py` checks independent physical/raw-count expectations, control
boundaries, deterministic noise, GNSS movement, timed faults and scenario export
followed by byte-identical regeneration through the actual CLI.

`test_hat_signals.py` exercises a fixed eight-second capture through production
Pi sensor drivers on modeled register/packet buses. It measures frequency, gain,
phase, gravity, gyro/tilt consistency, inter-IMU agreement, GNSS motion and sample
timing. Negative controls prove that physically wrong but well-framed data fail.
The software profile retains `hat-signals.ssrec` and `hat-signals.json`; the UI's
**Test HAT signals** button runs the same analyzer and displays its exact capture.
These thresholds apply to ideal models, not unqualified physical hardware.

Keep small deterministic input fixtures here. Put generated logs, traces and
coverage in the portable lab's disposable workspace. Reserve bounded waveform
capture for failures. Add runnable profiles when their implementations and
acceptance criteria exist; do not substitute placeholder passes for integration.

See the [simulation roadmap](../../docs/portable-lab.md#next-simulation-layers).
