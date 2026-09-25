# T1 physical bench procedure and report

This procedure qualifies the assembled Pi/T1/Trenz stack. It is separate from
preparing a prototype fabrication submission. Physical tests run when an assembly
exists; missing physical evidence is recorded as incomplete, not fabricated by a
simulation. The user owns fabrication approval.

## Prepare the report and instruments

Create one report folder under ignored `sw/build/` or dedicated lab storage.
Keep authored procedures here and raw captures outside Git. Retain the completed
report and its attachments with the hardware revision when the bench run ends.

```sh
mkdir -p sw/build/bench-001
python sw/tools/bench.py init sw/build/bench-001/report.json
python sw/tools/bench.py check sw/build/bench-001/report.json
```

The initial check intentionally returns **incomplete**, exit code 2. Record the
operator, UTC date, board serial/revision, software commit, Pi/kernel, GNSS firmware,
FPGA bitstream or explicit unconfigured state, instruments/calibration references,
mounting, cooling, temperature range, sample/filter settings and power cases.
Enter application targets for UTC error, inter-IMU skew, acceleration noise,
thermal bias change and FPGA noise ratio before evaluating those tests.

Use a current-limited adjustable supply, DMM, oscilloscope with suitable differential
voltage/current measurements, electronic load, logic analyzer, temperature probes,
calipers and an independent UTC/PPS reference. Timing qualification needs a shared
instrument timebase of known accuracy. Comparing the GNSS PPS only to itself cannot
establish absolute UTC accuracy. Motion tests also need known orientations and a
reference accelerometer/shaker for frequency/phase characterization.

Store scope exports, logic traces, `.ssrec` recordings, analyzer JSON and fit photos
inside the report folder. Generate each evidence entry with:

```sh
python sw/tools/bench.py evidence sw/build/bench-001/report.json sw/build/bench-001/trace.csv
```

Copy the returned relative path/hash into the relevant check's `evidence` list.
Every measured check needs evidence. The checker rejects missing/altered attachments,
outside-folder paths and wrong units. Files are capped at 64 MiB each. It checks
supplied measurements and evidence integrity; it cannot certify instrument setup
or infer physical truth from a filename.

## 1. Power and partial-power operation

1. Inspect assembly/polarity/shorts unpowered. Begin with Trenz unconfigured and
   external power current limited. J83 pin 1 is positive, pin 2 ground. Use the
   documented 3.35 V ±0.5% source; the Pi sensor supply remains separate.
2. Capture cold startup at J83, the module management rail and the sequenced I/O
   rail, plus input current and reset/enable/PGOOD where accessible. Evaluate
   ramp/sequence/reset behavior against the installed Trenz revision and regulator
   documentation. The ordinary operating minimum is not a requirement at t=0.
3. Once operating, measure minimum/maximum module management voltage during idle,
   intended FPGA load, Pi stress and 0.1↔3 A characterized load steps. Record
   actual edge rates and ringing. The simulation's 100 µs ramp is not a substitute
   for faster measured switching behavior. Avoid double-counting FPGA plus dummy
   load: the total initial operating envelope is 3 A.
4. After thermal settling, measure the complete positive-and-ground loop drop
   differentially at a known current: R = ΔV/I. Include connectors, fuse, copper
   and return paths. Record probe locations and uncertainty.
5. Repeat Pi-only, FPGA-only, both-powered and both turn-on/off orders. Capture
   leakage/back-power, reset/OE levels and interface behavior against component
   limits. Summarize `power_sequence` and `partial_power_isolation` only after all
   cases are covered, with individual traces in the evidence.

Fixed report limits: operating module rail **3.201–3.399 V** and hot loop
**≤0.030 Ω**. If limits fail, correct supply/path/decoupling/protection and repeat
affected cases. Document measured inrush and component temperatures in the notes;
they are evaluated against the actual component ratings, not invented thresholds.

## 2. Mechanical fit

Assemble the intended Pi, SSQ riser, T1, Trenz, cooler and all four intended FFCs.
Check full socket engagement and pin orientation, spacer seating without board
bow, fastener clearance, connector/cable withdrawal, minimum cable bend radius
from the selected cable specification, cooling access and JTAG access. Measure
closest gaps and record photos. The nominal Pi-to-HAT gap is 27.179 mm; fit depends
on actual socket seating/cooler/cables. A dimensioned mock-up can precede assembly.
Set `connector_cable_cooler_fit=true` only after the intended configuration fits.

## 3. UTC, IRQ and acquisition timing

1. Follow [Pi deployment](../sw/pi/deploy/README.md), then capture with `--fifo --utc`
   using [the timing workflow](utc-timing.md). GNSS lock must be established; all
   configuration keys must acknowledge/read back. Keep raw evidence even when
   correlation rejects an interval.
2. Capture DUT PPS and an independent UTC-labelled reference on the same scope.
   Decode the actual I²C TIM-TP/TIMEUTC stream alongside PPS. Establish the correct
   integer-second relationship and bound receiver queuing plus complete-read age
   across cold start, reacquisition and the qualified stress envelope. A bus
   transaction duration alone does not bound generation-to-read age. If that bound
   cannot be established, leave UTC qualification incomplete.
3. Record IRQ and SPI activity while stressing CPU, storage and network, with FPGA
   off, idle and active. Compare recorded hardware timestamp intervals against
   instrument time. Determine kernel PPS timestamp error, clock-rate drift,
   sample/filter latency, inter-IMU skew and per-sensor acquisition error bounds.
   Independent sensor oscillators and filter delays are not removed by PPS.
4. Stop/resume the acquisition process deliberately to delay service. Confirm
   buffered data survive within the configured capacity, and overflow emits a
   fault/missing marker with unknown physical loss. Capture GNSS disconnect/reset,
   loss of lock and reacquisition. No UTC may bridge rejected intervals. Saturated,
   missing and raw data must retain their existing meanings.
5. Fill a copy of the timing-policy template with measured bounds, margin, report
   reference and input-recording SHA-256. Correlate to a new recording. Replay it;
   compare UTC residuals to the independent reference and retain the correlation
   JSON. Populate maximum error/skew and recovery/loss checks in the report.

A reasonable starting experiment is 10 minutes per load state plus repeated cold
starts; extend it until thermal settling, operating extremes and required uptime
are covered. This is a proposed characterization duration, not proof of rare-event
failure rate. Choose timing targets from the research use case before acceptance.

## 4. Noise, thermal drift and FPGA coupling

Record identical sensor settings and rigid mounting with FPGA off, idle and active;
repeat with cooling off/on where thermally permissible. Keep external vibrations
and temperature traces as controlled as practical. Retain thermal settling and
stable intervals separately. Record known orientations and a reference vibration
input for axis, gain and phase checks; package axes are not automatically board axes.

```sh
python sw/tools/measure_hat.py sw/build/bench-001/off.ssrec --output sw/build/bench-001/off.json
python sw/tools/measure_hat.py sw/build/bench-001/active.ssrec \
  --baseline sw/build/bench-001/off.ssrec --output sw/build/bench-001/comparison.json
```

The existing analyzer reports nominal-SI mean, standard deviation, trend, gravity,
sample periods and gaps. It does not yet calculate spectral density or Allan
deviation. For band-limited acceptance, use a documented filter/spectral analysis
and retain its script/settings/output as evidence. Enter worst-axis RMS over the
declared common band, worst thermal bias change and worst active/off noise ratio.
Do not compare runs with different sample/filter settings or use motion-contaminated
standard deviation as a stationary noise floor. Reference calibration and absolute
accuracy remain distinct from repeatability/noise.

## Evaluate and prepare the prototype release

```sh
python sw/tools/bench.py check sw/build/bench-001/report.json
```

Exit 0 means every supplied measurement/evidence item and application limit passes;
exit 2 means incomplete or failed checks; exit 1 means malformed input. Missing
measurements, targets, context or evidence never become a pass. Correct failed
items and repeat the affected tests with traceable revisions.

For the next **prototype fab submission**, freeze the intended T1 revision and
actual stack/copper/dielectric values; reconcile GNSS geometry with that stack;
run the full CAD/build checks; review footprint pin numbering, BOM availability,
DNPs, drill/microvia instructions and mechanical fit; then export and independently
inspect Gerbers/drills, assembly drawings and placements from that same revision.
Retain hashes and a release manifest. Fabrication data has not been exported or
submitted by this software task. Keep the physical bench report pending until
boards arrive, rather than requiring completed-board measurements before making
the first prototype.
