# Artix-7 200T module selection

Research date: 2026-09-23. This shortlist led to the separate
[DAQHAT-01 Trenz carrier prototype](trenz-hat.md). The original A2 circuit and boards
remain separate. See DAQHAT-01's report for its current layout and validation limits.

## Recommendation

Use the **Trenz TE0712-03-81I36-A** as the leading candidate for the FPGA HAT
variant. Its fitted FPGA is **XC7A200T-1FBG484I**, and its module outline is
**50 × 40 mm**. It is the smallest documented candidate in this shortlist, not
a claim that no smaller product exists. Confirm procurement lead time before
freezing the footprint: indexed old and new Trenz storefronts disagree on stock.

The supplied Amazon link resolves to an A7-Lite-35T listing (ASIN B0H29TXS14).
Do not buy that SKU expecting a 200T. Microphase documents a separate 200T
A7-Lite configuration, but this does not establish the marketplace SKU's device.
The linked board's exact mechanical dimensions were not independently verified;
no percentage size reduction is claimed.

## Candidates

| Module | Fitted FPGA | Module outline | Useful interfaces |
| --- | --- | --- | --- |
| Trenz TE0712-03-81I36-A | XC7A200T-1FBG484I | 50 × 40 mm | 158 GPIO and JTAG through three board-to-board connectors |
| HuMANDATA XCM-114-200T | XC7A200T-1FBG484C | 54 × 43 mm | 128 GPIO through two board-to-board connectors; JTAG header |
| ALINX AC7200 | XC7A200T-2FBG484I | 55 × 45 mm | 180 3.3 V GPIO plus additional 1.5 V GPIO; JTAG access |

Sources: [Trenz exact SKU](https://shop.trenz-electronic.de/en/TE0712-03-81I36-A-FPGA-Module-with-AMD-Artix-7A200T-1I-1-GByte-DDR3L-32-MByte-Flash-4-x-5-cm),
[HuMANDATA product page](https://www.hdl.co.jp/XCM-114/),
[ALINX selection guide](https://alinx.com/public/upload/file/ALINX_SOM.pdf),
[ALINX user manual](https://www.alinx.com/public/upload/file/AC7200_UG.pdf).

These are core modules needing a carrier, not standalone development boards
with every external socket. GPIO can implement UART, application reset and
future SPI links in FPGA logic. For the present Groundlark architecture, HDMI,
Ethernet and microSD sockets are not required. This is an interface feasibility
assessment; no candidate has been wired to or tested with this HAT.

## Carrier requirements

The current design sends preprocessed sensor data from the Pi over 2 Mbaud UART.
Retain Pi GPIO14/15 for the data path and the existing reset/enable semantics.
Keep the remote magnetometer/infrasound head on its existing USB connection.
Do not add USB-C to the HAT.

For TE0712, follow the [manufacturer TRM](https://wiki.trenz-electronic.de/display/PD/TE0712+TRM):

- Provide correctly sequenced module and I/O supplies; the documented nominal
  management/main inputs are 3.3 V. Select 3.3 V-capable GPIO banks or translate.
- Bring JTAG and its reference voltage to an accessible programming header.
- Audit connector mating carefully: these hermaphroditic connectors swap
  odd/even pin numbers between module and carrier.
- Select exact connector heights and verify the vendor mechanical model,
  mounting, component clearances and cooling before routing.

Design a new FPGA power budget. The existing Coldfoot module's assumed 600 mA
envelope does not establish FPGA power requirements. Check Pi supply capacity,
regulator transients, connector current and thermal rise against the implemented
FPGA workload. Keep switching-current return paths away from sensor references.

Use a dedicated FPGA input for application reset; do not assume a module's
configuration/system-controller reset has the same semantics. If both ASIC and
FPGA can be populated, select their UART paths explicitly so outputs cannot
contend. Otherwise document mutually exclusive assembly variants.

The existing Coldfoot FPGA target is Nexys Video with an SBG484 package.
These FBG484 modules require new pin constraints and board clock/reset handling,
then synthesis, implementation, timing checks and host-protocol tests. A matching
200T density does not make the existing bitstream portable.

## Status and next design stage

Smaller core-module candidates are available for investigation, so adapting the
HAT to the linked 35T marketplace board is not the recommended fallback.
The subsequent DAQHAT-01 revision implements the selected module's carrier in atopile
and KiCad. Its verification is recorded separately in the DAQHAT-01 report; existing A2
validation does not certify an FPGA variant.

Additional source: [Microphase A7-Lite manual](https://fpga-docs.microphase.cn/en/latest/DEV_BOARD/A7-LITE/A7-Lite_Reference_Manual.html).
