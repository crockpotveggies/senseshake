# T1 engineering closure

**T1-GEO revision:** GNSS is removed; one external Racotech vertical geophone
uses an ADS122C04 input. See [current circuit, acquisition and validation](geophone-input.md).
GNSS/PPS/RF details below describe the preceding revision or legacy recordings.
The current physical bench template is version 2, with geophone response/noise/timing
checks replacing the GNSS UTC check.

**Current pre-fab assessment:** see the [four-check review](pre-fab-review.md).
It fixes two acquisition loss-handling defects and closes the six analog path
targets. Optional flex-harness fit remains conditional; see the
[selected assembly](stack-assembly.md). The GNSS/RF history below is retained for
traceability, not as evidence about the current T1-GEO. Current evidence has 6,444 copper
items; the earlier counts below refer to the preceding layout revision.

Fabrication process approval is owned by the project owner. This work concerns
the sensor HAT and its Trenz interfaces; Coldfoot and USB-head firmware are separate.
Analysis against the recorded stack is conditional on those stack parameters.
Physical measurements are never replaced by a simulated PASS.

| Item | Implemented correction | Remaining evidence |
| --- | --- | --- |
| GNSS RF | Widened the front trace from 0.300 to 0.388 mm: calculated 57.33 to 49.98 Ω. Moved a bend away from a return-plane void; 900 sampled center/edge points now lie over filled In2.Cu ground. | Actual dielectric properties, mask effects, connector/antenna launches and RF measurement. |
| Power | Defined a 3.35 V ±0.5% source, ≤30 mΩ total hot loop and ≤3 A envelope. Added four bounded load-step cases and 31 independent interface/bias pin checks. | Real module startup/inrush, hot path resistance, regulator stability, fast transients and temperature. |
| Fit | Added SSQ-120-02-G-D GPIO riser: 27.179 mm nominal Pi-to-HAT gap; 7.179 mm calculated clearance after connector, cable and tolerance allowances. Updated assembly BOM and 3D assets. | Selected Pi/cooler and installed cable trial; riser seating and spacer shims. |
| Acquisition | Added opt-in IMU FIFO, hardware timestamp mapping, IRQ hints, explicit overrun/gap rejection, Pi 4 five-select overlay and safe SPI binding. GNSS configuration/TIM-TP/TIMEUTC/PPS capture and bounded offline UTC association are implemented and modeled-test covered. | Actual Pi boot/bus throughput, physical sensor behavior and measured UTC/acquisition uncertainty bounds. |
| Measurement | Added stationary recording analysis: SI means, noise standard deviation, trend, gravity norm, sample periods, gaps and FPGA off/idle/active comparisons. | Physical recordings, alignment/calibration references and application acceptance limits. |

This table tracks engineering closure, not a purchase or fabrication authorization.

## Evidence and assumptions

The [engineering report](../hw/boards/shakesense-trenz-hat/engineering.json)
is generated from the routed board. The RF calculation uses εr=4.3, 35 µm copper
and 0.215 mm reference depth. It is an uncoated quasi-static microstrip model;
sampled plane continuity does not establish a complete electromagnetic solution.
The initially widened route passed KiCad DRC but failed the added return-plane
check, which is why the bend also changed.

The [power cases](../hw/simulation/trenz/results.json) contain six supply/load
corners, one deliberately rejected long-lead case, three UART cases and four
load steps. Transients assume 26.4 µF effective capacitance, 20 mΩ ESR,
50/200 nH path inductance and a 100 µs 0.1↔3 A ramp. These do not model the
Trenz regulator control loop or FPGA switching edges. The power correction is
an explicit external-source envelope, not new onboard reverse/overvoltage
protection. The bench source must supply those protections.

The 31-pin audit protects both voltage domains, OE defaults, open-drain reset
and supply routing. It verifies connectivity against separate expectations;
partial-power electrical behavior still relies on the selected components and
needs powered/unpowered bench checks.

The [verification record](../hw/boards/shakesense-trenz-hat/verification.json)
identifies the portable full run and exact copper replay. Native ERC/DRC have
zero violations and zero unconnected items. Rebuilding placement and importing
the complete SES reproduces all 5,316 tracks/vias exactly. The portable suite
also includes 14 hardware regressions, 41 bounded SPICE cases and the software
tests, including negative controls. Results are conditional on these models.

## Execute on the first assembled stack

1. **Power and isolation:** use a current-limited source; measure J83 and module
   rail differentially. Check cold startup and 0.1–3 A load changes, then hot
   steady state. Require the module management rail to remain 3.201–3.399 V and
   hot loop resistance ≤30 mΩ. Repeat Pi-only, FPGA-only and both-powered states;
   measure leakage/back-power against the selected parts' limits. A failed
   resistance or transient check requires a power-path change, not a relaxed
   rail limit.
2. **Fit:** assemble Pi → riser → T1 → Trenz with the intended cooler and four
   FFCs. Check seating, cable bend/withdrawal, accessible JTAG and no contact under
   fastener load. The model currently assumes a Pi 4, a 16 mm obstruction and
   1 mm cable allowance; it does not certify another cooler or a Pi 5.
3. **Acquisition:** follow [Pi deployment](../sw/pi/deploy/README.md). Run with
   FPGA supply off first, then idle/active. Check all identities and readback;
   compare IRQ and SPI traces to recorded samples. Delay service deliberately:
   buffered samples must survive within the bound and overrun must emit a fault
   plus unknown-loss marker. No fabricated timestamp or zero-loss claim is
   acceptable after a reset or overflow.
4. **Noise, drift and coupling:** record stationary runs with identical sensor
   settings and mounting. Capture a thermal settling interval and a stable
   interval in each FPGA state. Use `python sw/tools/measure_hat.py <recording>
   --baseline <off-recording> --output <new-report.json>`. Inspect per-axis
   mean/trend/noise, gravity norm, saturation, gaps and sample periods. Supply
   physical reference orientations and application limits before calling these
   measurements a pass. The analyzer uses nominal sensitivity and package axes;
   it does not estimate absolute alignment, spectral noise density or Allan
   deviation.

## Remaining software boundary

`live --fifo` is implemented and tested against modeled register buses; ordinary
polling remains available. The UI's HAT signal test still exercises its existing
polling-driver model. Separate FIFO integration tests cover buffered acquisition.
The GPIO event reader records PPS in kernel MONOTONIC and an estimated RAW domain.
The timed GNSS path now configures/read-backs the timepulse and records TIM-TP and
TIMEUTC evidence. [Offline correlation](utc-timing.md) can add UTC with explicit
uncertainty to a copy of a completed recording. It requires measured bounds,
rejects ambiguous intervals and preserves raw timing. NAV-PVT reception time is
not treated as the pulse timestamp. Software behavior is covered by modeled tests;
physical timing accuracy remains unqualified. The [bench procedure and report
checker](bench-procedure.md) make the remaining physical tests executable and
retain incomplete status when measurements or acceptance limits are absent.

Coldfoot, USB-head firmware and FPGA application bitstreams remain outside this
sensor-HAT correction. All 155 FPGA GPIOs and the original A2/head circuits remain
preserved. No fab approval has been requested or inferred.

References: [microstrip equations](https://qucs.sourceforge.net/tech/node75.html),
[ST FIFO application note](https://www.st.com/resource/en/application_note/DM00517282-.pdf),
[Samtec socket dimensions](https://suddendocs.samtec.com/catalog_english/ssw_th.pdf),
[TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf),
[SN74LVC8T245](https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf).
