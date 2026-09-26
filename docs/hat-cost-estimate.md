# DAQHAT-01 prototype cost estimate

Researched 2026-09-25. All amounts are **USD**, before shipping, taxes and
supplier-specific procurement charges. This is a planning estimate, not an
accepted JLCPCB quotation. No components have been reserved or ordered.

The current revision removes U20/C20-C23/R20 in addition to the earlier fourth
IMU removal. It saves $38.38 in IC cost plus five passives against the previous
$300-365 assembled estimate. These figures reuse the existing supplier price
snapshot and conservative setup allowances; they are not a fresh checkout.
See [the current circuit revision](inclinometer-removal.md).

Scope: the current six-layer DAQHAT-01 with **117 fitted components**.
The owner requests **one populated HAT**. The calculator prices a batch of five
bare PCBs; four remain unpopulated. Standard PCBA normally starts at two assembled
boards, so the one-piece case requires supplier acceptance. No quantity increase
is implied or authorized.

## Budget

| Item | Estimate |
| --- | ---: |
| Five bare six-layer ENIG PCBs | $49.10 |
| Components fitted to one HAT | $73-98 |
| PCB batch plus one set of components | $121.72-146.72 |
| Professional assembly/setup allowance | $140-180 |
| PCB batch, one component set and assembly | **$261.72-326.72** |

Round the working totals to **$122-147 without assembly** or **$262-327 with
assembly**. These ranges are not ceilings: minimum purchase quantities, spare
parts required for placement losses, global sourcing/consignment, and shipping
can increase the checkout total. The listed component prices mix distributors;
they are not prices locked into JLCPCB's assembly inventory.

Allocating one fifth of the PCB batch gives $9.82 of PCB cost per HAT, but the
initial order still pays $49.10. Do not use $9.82 as the one-prototype cash cost.

The PCB figure comes from the saved [JLCPCB calculator](https://cart.jlcpcb.com/quote)
estimate: 85 x 56 mm, six-layer FR-4 TG135, stock JLC06161H-3313, nominal 1.6 mm,
green/white, 1 oz outer / 0.5 oz inner copper, filled/capped through-vias, ENIG,
and standard lead time. No Gerbers were uploaded for that calculator estimate.
Its screenshot is local at `.local/cost-down/jlc-standard6-enig-stock-quote.png`.
See [fabrication settings](cost-reduction.md). Assembly rails/fiducials and final
CAM review may change fabrication pricing.

## Priced components

Exact BOM MPNs, using published small-quantity USD tiers. Extended values are
rounded for display; subtotal uses unrounded values. Linked pages are price
snapshots, not guarantees of future price or assembly availability.

| Part | Quantity | Unit price | Extended | Source |
| --- | ---: | ---: | ---: | --- |
| LSM6DSOTR IMU | 3 | $3.9232 | $11.77 | [LCSC](https://www.lcsc.com/product-detail/C2655100.html) |
| ADS122C04IPWR geophone ADC | 1 | $8.0565 | $8.06 | [LCSC](https://www.lcsc.com/product-detail/C2872338.html) |
| LSHM-150-04.0-L-DV-A-S-K-TR | 2 | $8.7400 | $17.48 | [DigiKey](https://www.digikey.com/en/products/detail/samtec-inc/LSHM-150-04-0-L-DV-A-S-K-TR/6163841) |
| LSHM-130-04.0-L-DV-A-S-K-TR | 1 | $5.9570 | $5.96 | [Samtec](https://www.samtec.com/products/lshm-130-04.0-l-dv-a-s-k-tr) |
| ESQ-120-23-G-D Pi socket | 1 | $10.0460 | $10.05 | [Samtec](https://www.samtec.com/products/esq-120-23-g-d) |
| ISO1640BDR | 1 | $1.8863 | $1.89 | [LCSC](https://www.lcsc.com/product-detail/C5122339.html) |
| TMUX1574PWR | 2 | $0.5512 | $1.10 | [LCSC](https://www.lcsc.com/product-detail/C2673443.html) |
| SN74LVC8T245PWR | 2 | $0.3511 | $0.70 | [LCSC](https://www.lcsc.com/product-detail/C27643.html) |
| TCA9534PWR | 1 | $0.7211 | $0.72 | [LCSC](https://www.lcsc.com/product-detail/C783615.html) |
| TXU0202DCUR | 1 | $0.7932 | $0.79 | [LCSC](https://www.lcsc.com/product-image/C5186957.html) |
| TLV1117LV33DCYR, TI | 1 | $0.3728 | $0.37 | [LCSC](https://www.lcsc.com/product-detail/C15578.html) |
| TLV803EA30DBZR | 1 | $0.3934 | $0.39 | [LCSC](https://www.lcsc.com/product-image/C5218924.html) |
| TLV809EA30DBZR | 2 | $0.3100 | $0.62 | [DigiKey](https://www.digikey.com/en/products/detail/texas-instruments/TLV809EA30DBZR/11310649) |
| Phoenix Contact 1715721 | 1 | $1.1600 | $1.16 | [DigiKey](https://www.digikey.com/en/products/detail/phoenix-contact/1715721/260631) |
| Phoenix Contact 1803439 | 1 | $1.1000 | $1.10 | [DigiKey](https://www.digikey.com/en/products/detail/phoenix-contact/1803439/260590) |
| **Priced subtotal: 15 BOM groups / 21 placements** | | | **$62.16** | |

The remaining 24 BOM groups / 96 placements use explicit planning allowances,
not claimed supplier quotes:

| Remaining components | Placements | Allowance |
| --- | ---: | ---: |
| EEPROM, transistor, two logic gates, ESD protector | 5 | $3-8 |
| 44 resistors, 42 capacitors and fuse | 87 | $4-12 |
| Two Samtec TSW headers and the JP1/J4 header placeholders | 4 | $3-8 |

This gives $72.16-90.16 before additional price/sourcing uncertainty; round to
$73-98 for planning. C90's exact C0G capacitor was out of stock at the checked
LCSC listing, so its reference price is not treated as an available quotation.
JP1/J4 need complete orderable MPNs and Q1 needs a manufacturer/full order code.
No alternate parts have been approved by this estimate.

## Assembly allowance

The [JLCPCB Standard PCBA price schedule](https://jlcpcb.com/help/article/pcb-assembly-price)
lists $51.12 double-sided setup, $16.42 double-sided stencil and $1.53 per feeder
type. Budgeting 33-37 feeder loads gives $50.49-56.61; together those account for
$118.03-124.15 before soldering, fixtures and inspection. The published small-batch
rigid fixture charge is $16.42, hand-solder labor $3.58, plus joint/inspection fees.
The $140-180 allowance covers variation in which operations/fixtures are billed.
Do not automatically add a flat handling fee: JLCPCB describes it as a conditional
shortfall relative to Economic PCBA. Only the actual assembly quote resolves fees.

Counting caveat found during estimation: `assembly-review.csv` labels the three
Samtec LSHM connectors J80/J81/J82 as THT because their footprints also have plated
mounting pads. Their 260 signal contacts are SMT. For costing, count 107 SMT-only
placements, three mixed-mount connectors and seven THT-only placements: 110
placements with SMT contacts, 33 distinct SMT MPNs and 37 MPN/side combinations.
Do not omit the connectors from feeder estimates. Their process assignment must
be reconciled in the assembly review before approving production placement.
The sealed review package is unchanged by this estimate.

## Exclusions and next quotation step

Excluded: Raspberry Pi, Trenz FPGA module, external Racotech geophone, mating
geophone plug/cable, GPIO riser, standoffs/cooling/enclosure/PSU, and the separate
USB magnetometer/infrasound head. This is the HAT price, not a complete station.
Also excluded: supplier-to-assembler freight, procurement/consignment fees,
placement-loss spares, tariffs, taxes, final shipping and physical qualification.

A firm total requires resolving the three sourcing placeholders, allocating the
actual BOM in JLCPCB's catalog or consignment system, confirming mixed-mount
assembly and rails, and obtaining acceptance of one assembled board (or owner
approval of a different quantity). Do not infer order approval from this estimate.

Population update: removed six fitted placements and one unique MPN group.
The BOM now has 39 groups and 117 placements. The passive and assembly allowances
are retained conservatively; only the $38.38 IC saving is subtracted from the
previous total. See the circuit revision for current verification evidence.
