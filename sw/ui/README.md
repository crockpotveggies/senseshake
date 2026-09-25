# Python sensor workbench

Run the root `ui.ps1` / `ui.sh` launcher. See the
[user and developer guide](../../docs/sensor-workbench.md).

- `main.py`: Python page construction, charts, board scene and user callbacks.
- `style.css`: visual styling and responsive layout; dark by default.
- `pyproject.toml`, `uv.lock`: isolated, reproducible optional UI environment.
- `check.py`: page-construction/asset-delivery smoke check.
- `assets/`: checked display assets and provenance, separate from editable CAD.
- [workbench.py](../pi/senseshake/workbench.py): bounded framework-independent
  simulation/recording/replay controller.
- [test_workbench.py](../tests/test_workbench.py): controller regression tests.
- [hat_signals.py](../pi/senseshake/hat_signals.py): measured HAT signal regression
  behind the **Test HAT signals** button, using production drivers on modeled buses.

The UI is authored in Python. NiceGUI supplies bundled browser components based
on Vue, Quasar, Three.js and ECharts. There is no custom JavaScript application,
Node dependency install, npm build, or separate frontend server in this project.
