# T1-GEO pre-fab engineering review

Review performed 2026-09-25 UTC. **The four reviews are completed, with open
findings. This is not a layout freeze or physical qualification.** The carrier
remains 85 Ã— 56 mm; all 155 FPGA GPIOs and the four aligned XYZ IMUs are retained.

The reproducible [calculation and geometry report](../hw/boards/shakesense-trenz-hat/prefab-review.json)
is generated read-only from the routed board. Run the full portable lab to repeat
the checks. A successful test run means the asserted checks passed; it does not
erase the open engineering findings below.

## 1. Geophone response, filtering, noise and recovery

Added 256 independent combinations of sensor resonance, sensitivity, damping,
coil resistance, series resistance, differential/common capacitance and bias
resistance. Eleven frequencies produce 2,816 analytical evaluations. The model
is symmetric; separate SPICE transients exercise asymmetric input components.
These are bounded corners, not an exhaustive parasitic or statistical model.

At 10 Hz, sensitivity at the ADC input spans **19.566â€“26.246 V/(m/s)**,
versus 22.994 nominal. At 4.5 Hz it spans **12.178â€“22.562 V/(m/s)**.
These figures exclude ADC filtering and calibration error. A single fixed
23.4 V/(m/s) conversion is inadequate around resonance.

Calculated passive thermal noise at 25 Â°C is about **0.202 ÂµV RMS**, integrated
over the whole passive RC response. Combining it with the ADC's typical noise
gives approximately **0.539 ÂµV RMS**. This is a planning estimate, not an
assembled-board guarantee; cable pickup, reference effects, bias-current noise,
resistor excess noise, temperature and FPGA interference remain outside it.

The ADC uses a linear-phase FIR with one-cycle settling. At its nominal 330-SPS
setting, the documented conversion interval is **3.04296875 ms**, or
**328.626 SPS** at nominal clock, and the filter's âˆ’3 dB bandwidth is **150.1 Hz**.
The Â±2% clock scenario spans approximately 322.1â€“335.2 SPS. See
[TI sections 8.3.4â€“8.3.6 and Table 12](https://www.ti.com/lit/ds/symlink/ads122c04.pdf).
The advertised configuration period remains nominal, not a calibrated clock.

The 662 Hz passive pole is not itself evidence of an aliasing error: the
delta-sigma modulator samples at 256 kHz. However, unwanted inputs near its clock
images need analog attenuation. The ideal passive model provides **51.8 dB**
at 256 kHz; roughly **194 ÂµV RMS** of differential interference there could
leave 0.5 ÂµV RMS before further effects. No exact FIR coefficients were obtained,
so the review does not invent a digital-filter simulation or certify stopband
rejection. Define the required science band and interference allowance, then
measure the complete transfer/alias response. Software filtering cannot undo aliasing.

Eight additional ngspice cases check startup and removal of 2 mV and 50 mV
differential pulses with rail/capacitance corners, asymmetric components and
connector leakage. Passive input recovery is within 0.5 ÂµV of baseline after
5 ms. Bias is within 15 mV of its final value at 300 ms; calculated full-scale
common-mode margin exceeds 1.08 V across the reviewed DC corners. The 50 mV
pulse exceeds ADC full scale: the model proves only passive-node recovery,
**not the ADC's overload recovery**. Coil inductance and cable parasitics are absent.

## 2. Acquisition timing and loss handling

Added an independently advancing ADC clock and wire-time model to the real
six-channel acquisition/recording path. Tests cover 100/400 kHz IÂ²C, oscillator
corners, other sensor service delays, 12/30/900 ms scheduler stalls, rollover,
loss reporting and continued operation. Completion timestamps and unknown loss
remain explicit. A separate real subprocess test checks that loss status survives IPC.

Two defects were fixed:

- Duplicate reads no longer restart the counter-wrap ambiguity timer.
- Conversion gaps no longer consume the hardware-reset budget. They produce
  explicit discontinuity/missing records; real communication failures still use
  bounded recovery. This prevents a busy host repeatedly resetting a healthy ADC.

**Polling is not qualified for complete capture.** In the declared deterministic
three-second workload, valid delivery was approximately 240â€“247 samples/s at
100 kHz, and 275â€“285 at 400 kHz. These are model results, not Pi benchmarks.
The model includes wire time and bounded competing sensor delays, but no real
Linux scheduling, IPC latency distribution or clock-stretching measurement.
Changing IÂ²C speed alone does not solve service jitter. The deployed overlay
remains 100 kHz; 400 kHz also needs rise-time qualification.

Use a dedicated acquisition worker driven by falling-edge DRDY, with a bounded
queue and explicit overflow reporting, for the next software iteration. Associate
edge timestamps only when conversion-counter continuity establishes which
conversion was read; queued edges cannot recover overwritten ADC samples.
BCM4 already receives DRDY through U42, so **no additional PCB pin is needed**.
Verify delivered rate and latency on the target Pi before making timing claims.

## 3. Components, pins and routed layout

The independent 51-connection geophone fixture is rerun, including the physical
TSSOP ADC, SC-70 protection device, connector polarity, supplies and DRDY path.
The review checks all 18 new BOM entries against explicit part/package fixtures.
This fixture check is distinct from supplier stock confirmation.

C90's original KEMET ordering code could not be confirmed from the current
manufacturer endpoint. It was replaced with documented production part
[TDK C3216C0G1H104J160AA](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216C0G1H104J160AA):
100 nF Â±5%, 50 V, C0G, 1206. The electrical value and existing 1206 land pattern
are retained; its maximum body height is 1.8 mm, outside the module footprint.
The generic KiCad capacitor body is not a certified supplier model.

C91/C92 retain the manufacturer's documented
[1 nF C0G 50 V part](https://search.kemet.com/component-documentation/download/specsheet/C0603C102J5GACTU).
Bulk capacitors are 10 V X5R; input filters are C0G. The SPICE bulk-capacitance
range is an assumption, not a measured DC-bias curve. Signal/resistor ratings
cover normal operation; this review does not qualify sustained external faults.
[TPD2E2U06](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf) suppresses handling ESD;
its clamp is not a 3.3 V precision limiter or lightning protector.

Measured copper paths (excluding pad interiors and via barrel length):

| Path | Length | Review |
| --- | ---: | --- |
| ADC AVDD to C95 | 0.90 mm | Pass: local bypass |
| ADC DVDD to C96 | 1.84 mm | Pass: local bypass |
| ADC AIN+ to C90 | 2.06 mm | Pass: final filter beside ADC |
| ADC AIN- to C90 | 2.54 mm | Pass: final filter beside ADC |
| J90 GEO+ to D90 | 1.77 mm | Pass: protection at connector |
| J90 GEO- to D90 | 1.78 mm | Pass: protection at connector |

**Analog path cleanup is complete.** C90 moved beside U22 on the front;
C95/C96 moved to the back with short supply connections, and D90 moved to the
back beside J90. Dedicated ground stitches are within 1.5 mm of all three
local ground terminals. The six paths now pass enforced project limits of
3 mm for bypass/filter and 5 mm for connector protection. These limits are
layout-review goals, not vendor noise guarantees. The direct filter and
protection segments are locked in the saved routing snapshot.

Ground-plane sampling is retained in the report. Uncovered samples near pads,
through-hole antipads and vias remain; the board is not being claimed as a
continuous-plane or field-solver signoff. Measure cable pickup and FPGA-on/off
noise on first articles. ADC supply-pin through-vias require filled/capped
via-in-pad processing; see the assembly notes.

## 4. Stack, connectors and service space

The selected module remains
[TE0712-03-81I36-A](https://www.trenz-electronic.de/en/FPGA-Module-with-AMD-Artix-7A200T-1I-1-GByte-DDR3L-32-MByte-Flash-4-x-5-cm/TE0712-03-81I36-A),
with standard 4 mm connectors and nominal 8 mm mated board separation. Do not
substitute the low-profile `-L` version without reviewing the stack.

The [selected assembly and cable-fit notes](stack-assembly.md) specify a Pi 4,
18 x 18 x 10 mm passive heatsink, Harwin M20-1060600 JTAG housing and Phoenix
1803581 geophone plug. The narrow JTAG housing leaves 0.75 mm lateral margin
after allowance; the geophone plug leaves 9.20 mm to the module. These
calculated envelopes are checked alongside actual board placements.

The identified ribbon interferences have a concrete CAD fix: J87 moves north
of the bypass capacitors, J83 moves left of the ribbon corridor, and a
windowed fourth spacer plus insulating guide preserves all four Pi supports.
The revised service view includes the flex paths. Use the specified short-tip
custom FPCs and [mechanical parts](../hw/mechanical/t1-ribbon-guide/README.md);
generic reinforced FFCs are not interchangeable. The geometry audit includes
actual underside courtyards, PTH ends, screw heads and spacer solids, with
regressions for the original collisions. First-article fit and the flex maker's
construction confirmation remain physical/procurement checks.

## Disposition

The software defects and six analog path-length findings are fixed. All 155
FPGA GPIOs and four aligned XYZ accelerometers are retained. Ribbon-clearance CAD checks cover the prescribed custom flex assembly;
physical harness fit remains to be measured. Dedicated DRDY acquisition is a software follow-up supported
by existing wiring. Physical transfer/noise, aliasing, power, thermal and timing
tests belong to first-board bring-up; the [bench procedure](bench-procedure.md)
retains those as pending.

Fabrication exports must use this updated placement and routing snapshot after
the final verification run. Fabrication process decisions remain with the owner.

## Validation record

See the [current verification record](../hw/boards/shakesense-trenz-hat/verification.json)
for the exact tested source hashes, full portable run, native ERC/DRC and clean
routing replay. The [retained acquisition stress results](pre-fab-acquisition-stress.json)
remain applicable to unchanged acquisition software. Layout changes do not
constitute new physical signal measurements.

Current run `20260925T161718Z-0cb993da`: 18 stages, 26 hardware regressions,
152 software tests, 64 SPICE cases; ERC/DRC/opens all zero. Clean replay matches
7,485 copper items including 46 microvias, with matching schematic links.
All geophone signal copper and the physical pad/net map are preserved.
Browser signal check: 10/10 passed across 3,672 samples.

The four flex paths pass all 36 slot-height cases. Minimum residual obstacle
margin is 0.234 mm after cable allowance; ribbon separation is 1.668 mm.
The guide clears the Pi port envelope by 0.379 mm after the 1 mm stack allowance.
These are CAD margins for the prescribed assembly, not physical measurements.
