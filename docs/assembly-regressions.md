# Assembly export regression coverage

Run `python3 -m unittest discover -s hw/tests -v` with KiCad 9's Python module
and `kicad-cli`, or run `./lab.ps1 test` in the portable environment.
These checks are offline and do not scrape stock or place orders.

Validated on 26 September 2026: all 22 portable full-profile stages passed
(`20260926T204143Z-ad55ecb7`), including 187 software tests. The final staged
checkout passes 124 hardware tests, including a further stale-design-input
regression, without any local release archives or caches. Lab runner tests
pass (14 passed; the Windows-only junction test is skipped in Linux).
Native BOM line endings are preserved in Git because validation hashes bind
their exact bytes; clean-checkout export is checked as well as working-tree export.

| Reported problem / method | Regression coverage |
| --- | --- |
| Value-only matching selected diodes, inductors, wrong capacitor packages/dielectrics and unreviewed IC manufacturers | `test_jlcpcb_bom.py`: independent exact manufacturer/MPN/C-number fixtures, source value/footprint/DNP guards, full-code official catalog URL checks and CSV round-trip |
| J1 was omitted or reverted to an unselectable part | J1 MPN/code propagation through every BOM/procurement field; missing code stays explicitly manual-sourcing instead of removing the socket |
| Supply capacitor and fuse shortages | Approved C42/C80-C82, C84/C85, C90 and F80 substitutions; documented manufacturer evidence; 1206 fuse lands reject the old 0603 part |
| C91/C92 catalog footprint unavailable | Exact KEMET alias C140950, retained filter specification, two pad checks per capacitor, no stale missing-footprint warning |
| J4/JP1/JP80/JP81/J80-J82 and J1 rotation errors | `test_jlcpcb_placement.py`: independent expected angles plus numbered-pin transforms; J1 bottom-only basis and fixed absolute coordinates |
| U102 and related bottom ICs | Local-X reflection before CCW rotation; pin-order and displaced-pad faults; U100-U103 expected angles and fixed body centres |
| False fixes / wrong library geometry | Scale, pitch, mirror, duplicate/missing contacts, displaced mounting pads, duplicate mappings, nonfinite or nonpositive SMT geometry; U40's two physical OUT lands checked |
| Repeated rotation corrections | Export is idempotent; nonpolar RC/fuse parts keep their native axis instead of arbitrary 180-degree flips |
| Supplier defaults to multiple HATs | `test_jlcpcb_quantity.py` and BOM tests enforce exactly one HAT and reject 2/5, floats and booleans; 117 unique placements / 38 BOM lines |
| Old corrections lost during regeneration | `test_jlcpcb_export_integration.py` creates a temporary real KiCad export, injects the old J1/C91/C92 selections and all 21 rotation errors, then compares the corrected BOM/CPL byte-for-byte with the full exporter |
| Stale or altered release inputs | `test_jlcpcb_bom_overlay.py`: base checksums, stale design rejection before output creation, immutable prior outputs; integration permits reviewed registry changes while checking unchanged artwork and ZIP members/checksums |
| Historic stock confused with allocation | BOM tests exercise zero and positive observations without changing fitted quantity or claiming allocation; purchase quantity stays TBD for MOQ/attrition |

All 117 installed components have exact catalog mappings, checking 703 physical
pads. Tests check public geometry, not the private supplier feeder/model library.
Review the order preview after clearing prior manual rotation overrides.

For every future substitution, record manufacturer, exact MPN/C-number,
specification/package, manufacturer evidence, dated catalog observation and
the reason for substitution in `hw/assembly/daqhat-01-jlcpcb-parts.json`.
Update the exact footprint mapping too: stale identities fail export. Freeze
the supplier PAD data, UUID, response hash and coordinate convention; never
apply an unexplained reference-specific angle offset.

At ordering time, recheck live **available order quantity**, minimum purchase,
assembly eligibility and fees for the exact part. A catalog listing or a
passing offline test does not establish current inventory or reserve it.
Generate a new ignored release directory, preserve prior packages, and review
BOM and CPL together. Native CAD, electrical specification and existing
physical/process holds must stay unchanged for a procurement-only overlay.
