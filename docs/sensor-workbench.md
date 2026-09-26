# Sensor workbench

**DAQHAT-01 revision:** GNSS is removed; one external Racotech vertical geophone
uses an ADS122C04 input. See [current circuit, acquisition and validation](geophone-input.md).
GNSS/PPS/RF details below describe the preceding revision or legacy recordings.
The current physical bench template is version 2, with geophone response/noise/timing
checks replacing the GNSS UTC check.

This is a functioning local Python/NiceGUI workbench for virtual sensor
experiments and validated recording replay. It defaults to dark mode and runs
without a Pi, FPGA or Coldfoot chip. Live hardware acquisition remains available
through the [existing Linux CLI](sensor-software.md); this UI does not yet attach
to physical devices.

![Actual dark-mode workbench with the DAQHAT-01 board and sensor traces](images/sensor-workbench.png)

## Start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) once, then:

```powershell
cd P:\Personal\groundlark
./ui.ps1
```

On Linux/macOS, use `sh ./ui.sh`. Open `http://127.0.0.1:8080` in a browser with
WebGL enabled. `./ui.ps1 -Port 8081` or `sh ./ui.sh --port 8081` selects another
port. Ctrl+C in the launcher terminal stops the server. It binds to loopback
only. First launch needs network access to install locked dependencies; normal
operation uses local assets and does not require a cloud service.

The launchers put Python, the UI virtual environment and uv's package cache in
ignored `.local/`. Windows and Linux have separate environments. Runtime schema
generation writes `sw/build/ui-schema.binpb` from the checked `.proto`; it does
not use or change the frozen compatibility baseline. Docker/atopile packages are
unchanged. `uv cache clean --cache-dir .local/uv-cache` clears only this project's
download cache; it does not remove saved recordings or the virtual environment.
Experiments stay in memory until downloaded. There are no per-run directories
to accumulate. Downloads go to the location selected by your browser.

## Run an experiment

1. Press **Load rocking + field demo**, then **Start**. Or select a seed and
   **New run** for the baseline gravity/field model.
2. Select an IMU on the board or in the device list. Its highlight and charts
   follow the selection. **Top** / **Orbit**, dragging and scrolling change only
   the camera. Selecting magnetometer/infrasound switches to the separate USB
   head view. The FPGA is not needed to run these models.
3. Expand stimulus groups. Set pose, sinusoidal vertical acceleration, XYZ
   magnetic field, sinusoidal pressure, geophone velocity/frequency,
   or per-sensor faults. Press the corresponding **Apply** button.
   Form values are proposed settings, not readbacks of a loaded waveform.
   Advanced noise, drift, pulse, multi-axis and timed controls remain available
   through [scenario JSON](stimulus-models.md), imported under
   **Recordings & scenarios**.
4. **Pause** freezes simulated time. **Finish & save** ends the run and downloads
   a `.ssrec` recording containing identities, effective configurations, samples,
   status, applied stimulus changes and completion summary. Capturing begins at
   time zero; no separate Record toggle is required. Download before starting a
   new run or closing/reloading the page. **Export scenario** saves the full
   schedule; reuse the same seed for deterministic results.
5. Open a `.ssrec` under **Recordings & scenarios**. Its CRCs and cross-message
   semantics are validated before the current run is replaced. Press **Play**
   or drag the timeline to seek. Stimulus controls are disabled in replay.
   Reaching the end pauses playback; seek backwards to play again.

Each tab owns an independent run. A disconnected tab pauses; refreshing starts
a fresh session. There is no persistent experiment database in this version.
The simulator stops after three simulated minutes or at its byte budget.
An exhausted retry budget requires a new run, as in the acquisition runtime.

## Data and timing

### HAT acquisition signal test

Press **Test HAT signals** in the top bar. Save your current experiment first:
the button replaces the displayed session with the test recording. This runs
eight seconds of simulated time faster than real time and loads the resulting
capture into replay. The pass/fail panel belongs to that capture and is cleared
when you start a different run or import another recording. Download the exact
recording and its JSON report using the panel buttons; the report includes the
recording's SHA-256. Seek backward and press Play to inspect the checked signals.

Unlike ordinary simulation, this test feeds the models through register/packet
buses into the production `LSM6DSO` and `ADS122C04` driver classes,
then through the acquisition, session validation and recording code. It checks
3,264 samples from the four HAT sensors. Remote-head sensors are outside this test.

The fixed excitation is a 2 Hz, 0.300 m/s² X-axis acceleration sine wave, 0.5 Hz,
5° roll, and a geophone input of 100 µm/s at 10 Hz. The independent recording
analyzer checks inventory/quality, effective configuration, sample timing and
continuity, tone frequency/gain/phase, gravity magnitude, prescribed roll,
integrated gyro versus gravity-derived roll, agreement across three IMUs,
and geophone gain/phase and conversion-counter rollover.
Measurements and explicit tolerances are expandable in the UI. These are
**ideal-model regression limits**, not manufacturing acceptance specifications.
Geophone excitation is commanded independently of HAT motion; the test does
not establish a shared mechanical mounting model.

![Current HAT driver signal test: nine passing checks without the inclinometer](images/hat-signal-test.png)

The portable software profile also saves `results/sw/build/hat-signals.ssrec`
and `hat-signals.json` in its retained run. After starting the UI once, the
same check can be run from the Windows UI environment:

```powershell
$env:GROUNDLARK_DESCRIPTOR = "$PWD/sw/build/ui-schema.binpb"
./.local/ui-venv/Scripts/python.exe sw/tools/check_hat_signals.py --output .local/hat-check.ssrec
```

Choose a new output filename for each manual run; existing recordings are never
overwritten. The signal regression tests include negative controls which alter
otherwise valid, CRC-correct records or excitation. Wrong frequency, gain,
polarity, motion, stuck channels, gyro scale, geophone polarity, timestamps
and missing measurements must fail. Existing independent bus-vector tests remain
the guard for wire constants/CRC logic shared by a driver and a modeled bus.
This does not exercise Linux ioctls, physical SPI/I²C timing, or real HAT noise.

### Display semantics

All six sensors use the existing `Acquisition`, `Simulated`, `Scenario`,
`Sessions` and CRC-protected recording code. The display does not generate a
second stream of decorative data. Stimulus changes are recorded before the
corresponding samples, and simulation steps are fixed at 1 ms. UI/wall-clock
delays slow the experiment; they do not change its sample values or create
invented timestamps. Camera movement never schedules stimulus changes.

Charts show native **raw counts**. Temperature registers are not silently converted to °C. Missing fields
are `null` chart gaps; valid zeros remain zeros. Saturation and fault labels are
visible. The geophone shows its conversion counter and signed ADC counts.
The pressure display preserves its raw status bits. This version does not plot
optional calibrated outputs or spectral estimates.

The time axis is recording **arrival time**, relative to the first record when
replaying. Pi and MCU acquisition timestamps remain intact in the recording;
the UI does not imply their clocks are synchronized. Replay supports recordings
up to 8 MiB and one hour in duration, including incomplete recordings with a
visible completion warning. Only 400 recent points per sensor and 20 recent
events are retained for display. The acquisition record itself is bounded at
8 MiB. Existing scenario limits (256 events / 8192 normalized bytes) apply to
interactive controls as well as imported scenarios.

The DAQHAT-01 3D asset comes from checked KiCad geometry, with simplified custom bodies
added in Python. The remote head is an approximate placement-based visualization
and shows the optional pressure sensor. See [asset provenance](../sw/ui/assets/README.md).
These views and ideal sensor models do not establish mechanical fit, magnetic
noise performance, electrical timing or fabrication readiness.

## Develop and test

The page is in [main.py](../sw/ui/main.py), with appearance in
[style.css](../sw/ui/style.css). Research logic belongs in the independent
[workbench controller](../sw/pi/groundlark/workbench.py) or
[stimulus models](../sw/pi/groundlark/stimulus.py), not in browser callbacks.
NiceGUI supplies the browser engine; all authored UI behavior is Python.

```powershell
# Full sensor/contract regression suite, including workbench controller tests
./lab.ps1 test -Profile software
# Actual NiceGUI HTTP page construction and board asset delivery
$env:UV_PROJECT_ENVIRONMENT = "$PWD/.local/ui-venv"
uv run --locked --project sw/ui python sw/ui/check.py
```

On Linux, set `UV_PROJECT_ENVIRONMENT="$PWD/.local/ui-venv-linux"` instead.
The optional UI environment has its own lock; dependency changes require
`uv lock --project sw/ui` and retesting. It does not rebuild the PCB or modify
atopile's dependency lock.

Controller tests exercise deterministic stepping, pause, controls, raw signed
values, missing-data gaps, no-fix behavior, bounded buffers, recording validation,
relative replay time, backward seeking, CLI scenario export, and run limits.
The HTTP smoke check does not test WebGL. Browser review must also cover board
picking, sensor switching, pause/resume, applied stimulus, downloads, uploads,
replay seeking and a narrow viewport before claiming the full UI works.

## Verified checkpoint

On 2026-09-24 the full portable run `20260924T225954Z-9c73b1f1` passed all
14 stages, including 94 software tests (14 new workbench tests), nine GPIO
fault fixtures and 37 SPICE cases. Lab cleanup tests passed 10 cases; the
Windows-specific junction case was skipped in Linux. Repository structure and
the separate NiceGUI HTTP/GLB smoke check passed. CAD authoring files are unchanged.

Browser checks covered sensor selection in the 3D board, remote-head switching,
pause/resume, a magnetic-field change, recording download and re-import, timeline
seeking and resumed replay. The downloaded 2,546-sample recording passed the
existing CLI validator with a completion summary. A 680 px requested viewport
showed the narrow layout without horizontal page overflow. This is UI and modeled
software evidence, not a claim about physical sensor or FPGA behavior.

The HAT-signal follow-up passed **107 software tests** in portable run
`20260925T024114Z-68747905` (2026-09-25 UTC), including 13 new driver/signal
regressions. Its ten quantitative checks passed on 3,672 samples. The UI button
was exercised in the browser; both downloaded artifacts matched an independent
recheck, including the recording SHA-256. The HTTP/GLB smoke check, repository
structure check and applicable cleanup tests also passed. No CAD source changed.
