# Reproducible A2 build

For validation in an isolated, portable environment, use the
[portable lab](portable-lab.md). It does not depend on the migrated local venvs.

The separate Pi-outline T1 build and rendering commands are in
[Trenz carrier documentation](trenz-hat.md#rebuild).

Used environment: WSL Ubuntu 24.04, atopile 0.15.9 with Python 3.14.7,
KiCad/pcbnew 9.0.9, ngspice 42 and Freerouting 1.9.0. The local atopile virtual
environment is `.venv-atopile`; it is a tool dependency, not part of the design.
Run these commands in Linux/WSL from the shakesense directory.

```sh
mkdir -p logs
CI=1 .venv-atopile/bin/ato build -v . > logs/atopile-build.log 2>&1
.venv-atopile/bin/python tools/solve_constraints.py > logs/constraint-solve.log 2>&1
.venv-atopile/bin/python tools/solve_constraints.py --negative > logs/negative-voltage.log 2>&1
python3 tools/simulate.py
python3 tools/assemble_pcb.py
```

`solve_constraints.py` explicitly invokes atopile's full numeric solver for
voltage/resistance/capacitance parameters. This is necessary because the stock
0.15.9 picker skips numeric solving for manually selected atomic components.
The negative case must reject 5 V applied to the 3.6 V IMU. No installed package
is patched and no electrical check is disabled. Component ratings use `assert
... within`; power sources specify their delivered range.

`assemble_pcb.py` resets routing, applies mechanical placement, adds the outline
and plane rules, and exports Specctra. It reads the compiled native KiCad board;
it does not create connections from a Python netlist. Save manual layout changes
before rerunning it. Electrical source is `elec/*.ato`; `layout.json` has no pin
net assignments. Review BOM presentation metadata when changing a selected MPN.

The checked route sessions are supplied with both boards. Reconstruct the
delivered layout after `assemble_pcb.py` with:

```sh
python3 tools/import_routes.py
python3 tools/trim_dangling.py
python3 tools/widen_power.py
python3 tools/review_schematic.py
python3 tools/models.py
python3 tools/check_circuit.py
python3 tools/check_design.py
python3 tools/report_validation.py
```

The HAT assembly step includes reviewed connector escapes and the short RF
trace; route sessions omit these fixed objects. Do not remove them before import.
The power-width pass tries 0.4/0.3/0.25/0.2 mm and uses native DRC to retain only
legal widening. Remaining 0.15 mm sections and per-net lengths are recorded in
`power-widths.json`; this is not an ampacity or extracted voltage-drop analysis.

For a changed placement/circuit, reroute each board and repeat the checks:

```sh
xvfb-run -a java -jar tools/freerouting-1.9.0.jar \
  -de hardware/shakesense-hat/shakesense-hat.dsn \
  -do hardware/shakesense-hat/shakesense-hat.ses -mp 25 -mt 1 -da
# Repeat for shakesense-field-head.
python3 tools/import_routes.py
python3 tools/trim_dangling.py
python3 tools/widen_power.py
python3 tools/review_schematic.py
python3 tools/models.py
python3 tools/check_design.py
```

The restricted SES importer verifies placements and rejects unsupported route
objects. The HAT session retains the previous routing with an explicit allowlist of removed cable parts/nets; fixed geometry includes the replacement ground-plane via. KiCad performs independent DRC afterwards. Review schematics use local
symbols with physical pin numbers, explicit no-connects and documented supply
flags. They are derived artifacts, not a second electrical source.

Routing needed interactive engineering decisions: restore the library U.FL
keepout, reserve the ground planes, and explicitly fan out three adjacent
mezzanine pins before routing their inner-layer connections. Autorouter
completion is never assumed from a successful process exit; the independent
unconnected-net check is required.

Render the actual PCB with KiCad (repeat for the field head):

```sh
xvfb-run -a kicad-cli pcb render --width 1800 --height 1000 \
  --quality high --background opaque --rotate 325,0,25 --zoom 0.9 \
  -o hardware/shakesense-hat/3d.png \
  hardware/shakesense-hat/shakesense-hat.kicad_pcb
```

The KiCad project opens directly in PCB Editor; use Alt+3 for its interactive 3D
viewer. Stock models require KiCad's 3D packages. Custom envelopes are portable
under `hardware/models/`. Prototype render geometry is not mechanical signoff.

Do not use the empty BOM emitted by atopile's automatic picker: this design uses
manual manufacturer parts. The explicit per-board `bom.csv` files are the review
BOMs. No purchase, assembly order or board fabrication was submitted.

Render the optional pressure sensor population with `python3 tools/render_option.py`. This changes only a temporary render board; U3 stays DNP in the delivered assembly.
