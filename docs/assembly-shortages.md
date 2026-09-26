# DAQHAT-01 assembly shortages, 26 September 2026

For the latest upload files, use the [placement correction](assembly-placement.md),
which includes these BOM substitutions plus the corrected connector rotations.

The assembly registry now explicitly selects the following replacements. The
source CAD MPNs remain the baseline design intent; the assembly registry records
each deviation and generates the supplier BOM. Copper, pads, position, polarity,
net connectivity and the per-board population of 117 components are unchanged.

| References | Old part/code | Selected part/code | Retained requirements |
| --- | --- | --- | --- |
| C42, C80, C81, C82 | GRM31CR61A226KE19L / C97950 | Samsung CL31A226KAHNNNE / [C12891](https://jlcpcb.com/partdetail/CL31A226KAHNNNE/C12891) | 22 uF, +/-10%, X5R, 1206; 25 V replaces 10 V |
| C84, C85 | GRM21BR71A475KA73L / C86039 | Murata GRM21BR71C475KE51L / [C408144](https://jlcpcb.com/partdetail/GRM21BR71C475KE51L/C408144) | 4.7 uF, +/-10%, X7R, 0805; 16 V replaces 10 V |
| C90 | C3216C0G1H104J160AA / C2168303 | Murata GRM31C5C1H104JA01L / [C97946](https://jlcpcb.com/partdetail/MurataElectronics-GRM31C5C1H104JA01L/C97946) | 100 nF, +/-5%, C0G, 50 V, 1206 |
| F80 | 0467005.NR / C187607 | Littelfuse 0466005.NRHF / [C57525](https://jlcpcb.com/partdetail/Littelfuse-0466005NRHF/C57525) | 5 A fast fuse; correct 1206 package, 32 V rating |

Live JLCPCB available-order quantities were 560,114 / 13,051 / 88,382 / 37,992,
respectively. Unit prices at quantity 1 were USD 0.1755 / 0.0619 / 0.1847 /
0.0707. Eight installed components total approximately USD 1.08 before attrition,
assembly/loading fees, tax or shipping. C12891 is Basic; the other three are
Extended. Stock was observed, not reserved; the actual order's allocation controls.

## Electrical and fit review

C42 is the sensor 3.3 V regulator output capacitor; C80-C82 bypass FPGA VIN;
C84/C85 bypass FPGA 3.3 V. Values and temperature classes remain unchanged.
The [Samsung specification](https://www.farnell.com/datasheets/3630670.pdf)
gives a 3.2 x 1.6 mm body and maximum 1.8 mm height. These use existing 1206 lands.
The selected Murata 4.7 uF part uses the existing 0805 lands. Increased voltage
ratings do not prove effective DC-bias capacitance or regulator transient response;
those remain part of the existing first-article power qualification.

C90 is across the differential geophone input. Its capacitance, tolerance, voltage
and C0G dielectric are preserved. No change to the modeled filter transfer function
is introduced. X7R/X5R and U2J are not approved substitutions here.

**F80 had a real package mismatch:** TZ_TZ_FUSE is a 1206 footprint, with pads
1.25 x 1.75 mm at 2.8 mm centre spacing, while the previous 467-series selection
was 0603. The selected [466-series manufacturer datasheet](https://www.littelfuse.com/assetdocs/fuse-466-datasheet?assetguid=dbe9bcd7-6072-4adf-bf5b-d33e52a6b90f)
specifies a 3.175 +/-0.127 x 1.524 +/-0.127 mm body. Its end terminations overlap
the existing pads. The manufacturer-recommended reflow pads differ slightly from
the generic KiCad lands; manufacturer assembly/fillet review remains required.
Do not assemble the legacy 0467005.NR named in the baseline schematic annotation.

The selected fuse retains 5 A fast-acting protection, with a 32 V rating and 50 A
interrupt rating. Manufacturer nominal cold resistance is 11 milliohms and
melting I2t is 1.6 A2s (June 2023 datasheet; the JLC summary shows a different I2t).
The prior fuse's clearing curve is not assumed identical. At the existing initial
3 A budget, nominal cold drop is 33 mV. The existing <=30 milliohm **total hot loop**
criterion still includes fuse, positive/return copper, cables and contacts; 11
milliohms is not a maximum hot resistance. Keep the current-limited supply and
measure voltage drop, temperature, inrush and fault clearing on first articles.
This is secondary protection, not an overvoltage or reverse-polarity device.

## Files and regression coverage

Use both BOM/CPL files from
`hw/releases/groundlark-daqhat-01-jlcpcb-placement-20260926-c91-c92/`.
This includes these eight shortage replacements, the later J1 C7499354 selection
and all connector/IC rotation corrections. C91/C92 additionally select
[KEMET C0603C102J5GAC7867 / C140950](https://jlcpcb.com/partdetail/KEMET-C0603C102J5GAC7867/C140950),
a manufacturer-documented alias retaining 1 nF / 50 V / C0G / ±5% / 0603, with
available catalog footprint data. JLCPCB showed 616 available to order at USD
0.0212 each (minimum one) on 26 September 2026; no stock was reserved.
Use the `20260926-one-hat` review package's Gerber ZIP; do not
reuse its older BOM/CPL. The overlay tool checks all original design hashes, exact
BOM/CPL reference sets, bottom-mounted J1, CSV serialization and ZIP integrity.
Packages remain local and Git-ignored.

The exporter now rejects recognized chip-package mismatches, including the custom
F80 footprint. Regression tests cover the previous 0603/1206 error, native F80 pad
geometry, each exact approved replacement, undocumented substitutions and unchanged
one-HAT counts. These tests do not constitute physical qualification.
