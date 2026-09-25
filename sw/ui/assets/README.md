# Board visualization provenance

`t1.glb` is a display asset exported with KiCad 9.0.9 from the checked T1 PCB.
It includes the routed board's outline, holes, pads, mask, silkscreen and available
stock component models. It is not a manufacturing deliverable.

KiCad's exporter cannot convert the local VRML bodies. The Python scene adds
simplified envelopes for the Pi socket, Trenz connectors,
SCL3300. Selection rings use `hw/layout-trenz.json` XY values.
The remote head is a separate placement-based schematic 3D view; its optional
pressure sensor is shown even though the default assembly is DNP.

Regenerate from the repository root on the Linux lab toolchain:

```sh
kicad-cli pcb export glb --force --no-dnp --include-pads --include-silkscreen \
  --include-soldermask --subst-models --output sw/ui/assets/t1.glb \
  hw/boards/shakesense-trenz-hat/shakesense-trenz-hat.kicad_pcb
```

The exporter reports missing local VRML models and returns 1 despite creating
the GLB. Inspect the result and missing-model inventory before accepting it.
Do not ignore other export failures. The scene converts GLB metres/Y-up to
centimetres/Z-up, subtracts the CAD origin (50, 50 mm), then centres the 85×56 mm
board. The placement coordinates themselves are unchanged.

`provenance.json` pins the PCB, placements and display asset. Update its SHA-256
values only after re-export and alignment review. Startup fails on stale inputs.
Stock KiCad component geometry retains its upstream attribution/license; see
[KiCad's library licensing](https://www.kicad.org/libraries/license/).
