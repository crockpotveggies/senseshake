# Groundlark naming migration

Groundlark replaces the previous ShakeSense/SenseShake project names. The GitHub
repository is `crockpotveggies/groundlark`; the Windows checkout is
`P:\Personal\groundlark`. The rename changes branding and identifiers, not sensor
selection, pin assignments, PCB placement, copper routing or electrical limits.

The sensor carrier model is **Groundlark DAQHAT-01**. Its former T1 name is
retired. Source filenames use `daqhat-01` and code identifiers use `daqhat_01`;
PCB revision and FPGA device choice are separate from the model name.

Current entry points use:

- Python packages `groundlark` and `groundlark_contract`.
- Protobuf package `groundlark.sensor.v1` and corresponding source directory.
- Environment variables beginning `GROUNDLARK_`.
- Docker image `groundlark/lab:1` and Groundlark container labels.
- KiCad projects `groundlark-hat`, `groundlark-field-head`,
  `groundlark-daqhat-01`, with the `Groundlark` symbol/footprint libraries.
- Device-tree overlays `groundlark-daqhat-01-overlay` and `groundlark-fpga-overlay`.

Rerun `./lab.ps1 build` (or `./lab.sh build`) to create the renamed Docker image.
Use the new Python import paths and environment variables in local scripts.
Rebuild/redeploy overlays under their new names using the deployment guide.
Old installed overlays and third-party Python import paths are not automatically
rewritten on another machine. Virtual environments and tool caches stay ignored.

## Compatibility and historical evidence

The binary recording magic `SSREC01`, `.ssrec` extension, frame format, field
numbers and types are unchanged. New captures use `groundlark-acquisition-v1`
metadata; the CLI, workbench and measurement tools also accept the former
`senseshake-acquisition-v1` label. Device identifiers inside historical recordings
are data, not strings to rewrite.

`sw/interfaces/baseline.binpb` remains byte-for-byte unchanged. The compatibility
gate creates an ignored descriptor projection with only the authorized package,
schema-path, qualified-type and `BOARD_T1` to `BOARD_DAQHAT_01` enum-symbol rename.
The board enum's wire value remains 1. Buf checks that projection against the
current schema, and the existing incompatible-field mutation must still fail.
Independent tests pin the original baseline hash and compare old/new encoded
messages. There is no new baseline that could hide a field/tag break.

Existing `.senseshake-lab` ownership markers and historical run owners are
accepted explicitly; their original identities are preserved. New lab directories
and runs use Groundlark. Cleanup still validates markers, paths and locks before
deleting anything. These narrow compatibility strings and the frozen descriptor
are intentional exceptions to the rename.

Third-party references and upstream attribution retain their original names.
Old local fabrication packages are superseded snapshots, not silently relabeled
as newly validated files. Regenerated Groundlark packages remain in ignored
`hw/releases/`; publishing them still requires an explicit request.

Fresh hardware/software validation and refreshed 3D/preview assets establish the
renamed project state. Physical qualification and supplier manufacturing holds
remain open; changing the name does not change those conclusions.

## Rename validation

The full portable run `20260926T013300Z-5e8c2946` passed all 22 stages,
including 43 hardware and 185 software regression tests. Native ERC/DRC and
route replay pass. Vivado rebuilt the renamed design; timing passes at 50 MHz.
The browser passed all 10 modeled HAT signal checks (3,672 samples); no physical
hardware was connected. Lab safety tests pass on Linux and Windows, with
platform-specific skips covered on the other host.

[The board comparison](groundlark-rename-validation.json) verifies unchanged
copper, component positions, pads and net assignments against commit `d3863e7`.
After normalizing authorized naming changes, the native PCB files are identical
except for moving the longer DAQHAT-01 front label 4 mm right to clear JP1.
Fresh renders and the UI display asset include that silkscreen change.
