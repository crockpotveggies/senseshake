# Software validation

The runnable contract suite (`test_contract.py`) uses an independently specified
binary producer fixture and covers semantics, corruption and bounded framing.
Run `./lab.ps1 test -Profile software` from the repository root.

The acquisition, driver and Linux I/O suites run the actual application against
independent expectations: recordings, bus errors, time jumps, malformed frames,
queue limits, disconnects, a real pseudo-terminal and a hung subprocess. The
portable runner retains a bounded demo recording and replay summary.
See [the runtime guide](../../docs/sensor-software.md) for limits and commands.

Keep small deterministic input fixtures here. Put generated logs, traces and
coverage in the portable lab's disposable workspace. Reserve bounded waveform
capture for failures. Add runnable profiles when their implementations and
acceptance criteria exist; do not substitute placeholder passes for integration.

See the [simulation roadmap](../../docs/portable-lab.md#next-simulation-layers).
