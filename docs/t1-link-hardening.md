# T1-LINK hardening and prototype preparation

Review date: 2026-09-25. Scope: the sensor HAT with internal Pi 4 / TE0712-03-81I36-A
SPI, UART and switched JTAG. Coldfoot integration is deferred. The full lab also
rechecks the unchanged A2 and USB-head circuits.

**Disposition: ready to prepare a small T1 prototype fabrication package.**
The final full run `20260925T214440Z-e4e115ce` passed all 22 stages: 33 hardware
regressions, 181 software tests, 102 SPICE cases and zero native ERC/DRC/unrouted
findings. Clean replay matches all 7,522 copper objects, including 11 microvias.
Twelve lab-safety cases are covered across Windows/Linux (platform-specific
skips pass on the other host). All 10 modeled signal checks pass over 3,672 samples.
This is not physical qualification or a released manufacturing package.

## Findings fixed

| Finding | Change and regression |
| --- | --- |
| A ready response arriving after the processing deadline could be accepted | Check time before and after each poll; boundary/late-response tests preserve the unacknowledged result. |
| A dropped ACK could be reported as success | Require an empty status after ACK; inject dropped ACK and transfer failures at all six stages. No automatic uncertain-write retry. |
| Reset during an asserted CS left a spurious sticky error | RTL discards the interrupted transaction through CS release; reset also releases MISO. Co-simulation checks reset during submit, read and ACK, followed by a successful fresh exchange. |
| Driver-restoration failure was not explicitly latched as faulted | Latch faulted ownership and reject reuse after cleanup failure; retain independent GPIO/I2C disarm attempts. |
| Normal service termination bypassed Python cleanup | SIGTERM now unwinds through isolation; regression verifies disarm, release and signal-handler restoration. SIGKILL/crashes still have no hardware watchdog. |
| Two PCB value fields were blank | Restore hidden U106/C106 values to match the correct authored parts and BOM. Copper, placement and visible geometry are unchanged. |
| New link parts lacked an independent purchasing/package check | Check all 32 link components across authored metadata, BOM and PCB, including required population; inject wrong supervisor, package, resistor value, DNP and duplicate-reference faults. |
| Routing replay ran only on the workstation | Stage the complete SES and run clean reconstruction in full/quick profiles. Add the missing hash-pinned system-Python parser dependency. |
| Timing reports could become stale or lack coverage | Gate implementation on timing coverage, setup/hold paths, reported CDC warnings and DRC findings; portable checks validate exact source/report hashes and reject missing/invalid evidence. |
| Bench checklist still described ribbon cables and omitted internal-link measurements | Version 3 requires physical JTAG, mode handoff, loopback and six SPI timing measurements; old/incomplete reports cannot qualify this revision. |

## Coverage and evidence

The [hardware verification record](../hw/boards/shakesense-trenz-hat/verification.json)
retains the portable run, input hashes and native results. The
[FPGA implementation record](../sw/fpga/verification/result.json) pins the actual
Vivado source, timing/CDC/DRC reports and generated bitstream hash.

| Layer | What is exercised | Boundary |
| --- | --- | --- |
| Circuits and PCB | Three Atopile builds/constraint solves, invalid-voltage rejection, independent pin/component fixtures, native ERC/DRC/connectivity, all 260 Trenz contacts, outline/stack/assembly envelopes and clean routing replay | No assembled-board electrical or fit test |
| Analog and power models | Existing support/geophone SPICE cases, 256 analog tolerance corners and 38 link switch/RC cases | Idealized switches, lumped loading and bounded sources; no extracted SI/PI or transistor-level brownout model |
| Sensor acquisition | Production drivers on modeled buses; signal gain/frequency/phase/axis checks; independent ADC clocks, FIFO loss, corruption, overload, stalls, worker IPC, replay and recovery | Does not measure sensor noise, Pi scheduling limits or physical buses |
| FPGA protocol | Existing 23 RTL status/read checks plus production Python-to-RTL pin co-simulation: all 193 payload sizes, sequence wrap, 20 fabric-clock phases, asymmetric SCLK duty cycles and 491 fault/reset cases | Deterministic digital simulation; no metastability/board timing claim |
| FPGA implementation | Vivado 2025.2, XC7A200T-FBG484-1, 50 MHz; setup +10.143 ns, hold +0.109 ns, pulse width +9.5 ns; no internal unconstrained endpoints or DRC findings | Intentional asynchronous input/reset exceptions remain; no physical programming test |
| Host robustness | Failed/short transfers at every stage, stale results, deadline boundary, lost ACK, I2C readback/disarm faults, ownership restore, termination cleanup and bounded polling | Mocked ownership plus Linux ABI/overlay tests, not a booted Pi kernel |
| Workbench and tooling | Controller/signal tests, real HTTP page/model delivery, structure checks and cleanup/ownership tests on Windows and Linux | No new browser interaction or physical sensor capture in this review |

The UI model was re-exported after the hidden PCB-value corrections. Its scene
nodes and binary geometry match the previous GLB exactly; only export metadata
differs. The existing display asset and renders remain valid, with updated provenance.

This is a bounded regression suite, not an exhaustive proof of every possible
input, electrical fault or operating condition. The portable FPGA evidence step
checks a recorded Vivado build; it does not run synthesis inside Docker.

## Next: prepare the prototype package

1. Freeze the tested T1 revision and exact assembly: Pi 4, specified riser and
   four supports, standard-height TE0712-03-81I36-A, geophone connector and
   selected cooler. Keep the FPGA at the top. Native quad and FPGA acceleration
   are not implemented; the initial application link is ordinary SPI up to 1 MHz.
2. Finalize the documented eight-layer 1+6+1 stack and fabrication drawing.
   Include filled/planarized microvias and filled/capped solder-pad through-vias,
   including ADC supply pads and U101.4. Preserve the recorded drills, copper,
   1.6 mm thickness, connector positions and board outline.
3. Review procurement BOM, exact package variants, population/DNPs and the
   geophone/power plugs. Export Gerbers, plated/non-plated drills, BOM, placement
   data and top/bottom assembly drawings from that frozen board.
4. Independently inspect those exports against the native CAD and assembly:
   layer order, outline/cutouts, hole sizes/plating, mask/paste, connector parity,
   bottom-side rotation and via processing notes. Hash the release files and
   retain a manifest tied to the commit. Then submit the prototype package.

These are release-preparation tasks. The test run does not itself generate or
approve that package. Fabrication decisions remain with the project owner.

## First-article qualification remains open

Use the [version-3 bench procedure](bench-procedure.md); blanks and missing evidence
must remain incomplete. Before evaluating captures, define the application noise,
timing/skew, thermal drift and FPGA interference limits.

- **Power:** verify both power-up/down orders, rail ramps, partial-power isolation,
  inrush and load transients. Supply J83 at 3.35 V ±0.5%; operating module rail
  must stay 3.201–3.399 V, with a measured total hot loop at most 30 mΩ within
  the initial 3 A envelope. The board's resistance/temperature is not extracted
  or measured; the external source supplies current limiting and polarity/OVP protection.
- **Fit:** verify actual socket engagement, four support clearances, cooling,
  geophone/power-plug access and board bow. CAD envelopes are not a seating test.
- **Programming and transport:** verify Pi GPIO ownership and Linux driver
  handoff, real IDCODE/volatile programming, switch isolation, at-pin timing and
  a recorded valid-traffic loopback soak under sensor/CPU load. Investigate every error.
- **Signals:** measure geophone polarity/gain/response, shorted-input and connected
  noise, clipping/recovery, conversion loss and IMU timing/axes; repeat with the
  FPGA off, idle and active and across the intended temperature range.

The remote USB sensor head still needs MCU firmware and physical USB enumeration
testing. Its circuit checks do not make it a functioning, qualified USB product.
The deferred A2/Coldfoot board is not the recommended first T1 fabrication release.
