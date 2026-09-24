# Software validation

Planned suites should run actual software against independently specified
fixtures: recorded sensor samples, bus errors, time jumps, malformed frames,
buffer limits, USB disconnects and accelerator backpressure.

Keep small deterministic input fixtures here. Put generated logs, traces and
coverage in the portable lab's disposable workspace. Reserve bounded waveform
capture for failures. Add runnable profiles when their implementations and
acceptance criteria exist; do not substitute placeholder passes for integration.

See the [simulation roadmap](../../docs/portable-lab.md#next-simulation-layers).
