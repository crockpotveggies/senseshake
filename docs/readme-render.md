# README hardware illustration

The single README image is rendered from the latest
`hw/boards/groundlark-daqhat-01/pi-trenz-stack-concept.kicad_pcb` assembly.
The routed HAT is the current three-IMU, no-inclinometer, six-layer revision;
the Trenz module uses the existing manufacturer STEP. The Raspberry Pi,
spacers and socket use the established dimensioned stack envelopes.

The added Racotech RGI-4.5Hz vertical geophone has the documented nominal
25.4 mm diameter and 33 mm body height. Its cap, terminal locations, mating
plug and lead routing are illustrative. The bare element is shown beside the
stack for clarity; it needs a firm holder in actual use. No external FPGA
ribbons are shown or required.

The stack still depicts the baseline Samtec socket. The shorter J1 procurement
substitute needs riser/height review; this illustration does not qualify it.

Rebuild with KiCad 9, its `pcbnew` Python module and `xvfb-run` on Linux/WSL:

```sh
python3 hw/tools/render_readme_stack.py
```

The script reads source CAD without changing it, stages its visualization board
and VRML in ignored `.local/readme-render/`, and writes the PNG plus
[source hashes and limitations](images/groundlark-stack-geophone.json).
It checks source hashes after rendering. Review the generated image before
publishing it. No Gerbers or assembly packages are generated.
