# T1 internal FPGA link: QSPI pin reservation and ribbon removal

Status: **planned revision, 2026-09-25; not yet implemented in Atopile or KiCad**.
The routed T1-GEO board and its renders still describe the previous expansion
revision, commit `64d4190`. Its validation does not cover this proposed circuit.

## Decision

Keep the Pi 4 / 85 x 56 mm sensor HAT / TE0712-03-81I36-A stack. Reserve six
Pi signals for a four-data-line SPI interface and keep the existing two-wire
UART. Remove external GPIO expansion J85-J89, including the four blue flex
cables, their guide and the offset/windowed Pi spacer. Restore four straight
Pi supports after checking their clearances. Retain the geophone, sensors,
power connector and Trenz mezzanine connectors. Coldfoot remains deferred.

JTAG programming from the Pi must also work through the stack, with no external
programming cable required. A switched connection shares four data-link pins
with JTAG; application transfers pause during programming. A small unpopulated
service footprint/test pads may remain for recovery, with explicit isolation
from the Pi programmer. No USB bridge or HAT USB connector is needed.

## What this wiring can do

On Pi 4, use **SPI6 with one chip select** for initial transfers. Its four
signals fit the six reserved pins and its Linux driver supports DMA. Sensor
acquisition keeps SPI0, its five chip selects, interrupts, and I2C unchanged.
Do not enable SPI6 CE1: GPIO27 belongs to IMU1. SPI1 occupies the same primary
pins but lacks DMA support in the current driver; it is not the preferred bus.
See the [Pi SPI documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#spi)
and [official SPI6 one-CS overlay](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/arch/arm/boot/dts/overlays/spi6-1cs-overlay.dts).

**Six wires reserve QSPI connectivity; they do not make the Pi 4 controller
quad-capable.** Its supported SPI driver does not provide four-bit transfers.
Initially DQ0 is MOSI and DQ1 is MISO, with DQ2/DQ3 idle. A real quad mode needs
a separately implemented and qualified host engine or a host/bridge change.
GPIO bit-banging may exercise quad protocol at low speed, but is not a promised
high-throughput transport. See the [Pi controller driver](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/drivers/spi/spi-bcm2835.c).

The FPGA needs an application SPI/QSPI **slave** in programmable logic, distinct
from its configuration flash interface. AMD AXI Quad SPI supports quad master
mode, not a drop-in quad slave. Use reviewed custom or suitable third-party
slave RTL for quad operation. See [AMD PG153](https://docs.amd.com/r/en-US/pg153-axi-quad-spi/Feature-Summary).

Quad payload transfers share four bidirectional lines and are half-duplex.
Do not promise simultaneous four-bit input and output, a fourfold end-to-end
speed gain, or a qualified clock rate from the pin count alone.

## Physical pin budget

The existing Atopile J1 has exactly six unconnected GPIO contacts: physical
pins **12, 32, 35, 36, 38, 40**. None is power, ground, HAT EEPROM, or a sensor
signal. The following assignment consumes all six while retaining UART.

| Application function | BCM GPIO | Pi J1 physical pin | Programming function |
| --- | --- | --- | --- |
| SCLK | 21 | 40 | JTAG TCK |
| CS_N | 18 | 12 | Application CS held inactive on FPGA side |
| DQ0 / SPI MOSI | 20 | 38 | JTAG TDI |
| DQ1 / SPI MISO | 19 | 35 | JTAG TDO |
| DQ2 | 16 | 36 | JTAG TMS |
| DQ3 | 12 | 32 | Application path isolated |
| UART Pi TX / FPGA RX | 14 | 8 | Retained |
| UART Pi RX / FPGA TX | 15 | 10 | Retained |

The other header GPIOs retain these assignments:

| Function | BCM GPIOs |
| --- | --- |
| HAT EEPROM | 0, 1 |
| Sensor I2C | 2, 3 |
| Geophone DRDY | 4 |
| Sensor SPI0 MISO / MOSI / SCLK | 9, 10, 11 |
| IMU1-4 chip selects | 8, 7, 5, 6 |
| Tilt chip select | 13 |
| IMU1-4 interrupts | 27, 22, 23, 24 |
| FPGA reset | 17 |
| Existing FPGA UART buffer enable | 25 |
| Sensor isolation enable | 26 |

Accounting: 2 EEPROM + 16 sensor/control + 4 existing FPGA/UART/control +
6 new link = **28 GPIOs**. No spare dedicated Pi interrupt or JTAG pins remain.
Read FPGA ready/FIFO status over SPI, or send bounded status over UART; do not
silently allocate another header pin. An I2C control expander supplies the
switch controls without consuming a new GPIO. Reserve a free address, nominally
0x20; select and check the part/address straps during circuit implementation.
The existing geophone ADC is 0x40 on I2C1; EEPROM uses the separate ID bus.

## Trenz connector reservation

All six proposed application pins are available bank-14 user I/O currently
routed to J87. Removing that connector releases them. Preserve the existing
UART/reset pins. The carrier mating footprint swaps odd/even contact numbers:
do not copy module pin numbers directly into the carrier footprint.

| Function | Trenz module contact | Carrier contact | Module signal |
| --- | --- | --- | --- |
| SCLK | JM2.22 | J81.21 | B14_L12_P, FPGA W19, MRCC |
| CS_N | JM2.24 | J81.23 | B14_L12_N |
| DQ0 | JM2.21 | J81.22 | B14_L14_P |
| DQ1 | JM2.23 | J81.24 | B14_L14_N |
| DQ2 | JM2.25 | J81.26 | B14_L13_P |
| DQ3 | JM2.27 | J81.28 | B14_L13_N |
| UART FPGA RX | JM2.11 | J81.12 | B14_L8_N |
| UART FPGA TX | JM2.13 | J81.14 | B14_L8_P |
| Application reset | JM2.14 | J81.13 | B14_L10_N |
| JTAG TMS | JM2.93 | J81.94 | Dedicated JTAG |
| JTAG TDI | JM2.95 | J81.96 | Dedicated JTAG |
| JTAG TDO | JM2.97 | J81.98 | Dedicated JTAG |
| JTAG TCK | JM2.99 | J81.100 | Dedicated JTAG |

Reservations are checked against the [vendor schematic](vendor/trenz/SCH-TE0712-03-81I36-A.PDF),
the existing [module I/O fixture](trenz-gpio-module.csv) and
[module/carrier map](trenz-pin-map.json). Bank 14 remains at the existing 3.3 V
I/O supply. Retain FPGA JTAG selection through the Trenz CPLD, configuration
reset and power sequencing. Check every FPGA package pin in the XDC against
the exact module variant before synthesizing; only the selected clock pad's
package assignment is specified here.

## Switching and electrical requirements

Use a bidirectional, break-before-make signal switch for the four shared pins,
plus isolation for CS_N and DQ3. Do not tie application pins directly to JTAG
pins or use the existing fixed-direction UART translator for quad data.

The Pi-powered I2C expander controls mode and link enable separately. Hardware
pulls must default the link to isolated even while the expander pins are inputs.
Power-good gating must prevent back-powering either unpowered board, including
through switch control inputs. Keep the existing UART isolation/enable circuit.
Choose switch parts with documented bandwidth, capacitance, off isolation and
power-off protection for the actual 3.3 V domains. Include local decoupling,
defined CS/TCK/TMS idle states, and configurable series damping footprints.
Determine resistor values and allowed clock from timing and signal integrity.

Programming sequence:

1. Exclusively lock the link, stop transfers, deassert CS and isolate it.
2. Release SPI6's driver/pin ownership before requesting GPIOs for JTAG.
3. Set safe GPIO directions (TDO input) and select JTAG while isolated.
4. Enable the programming path and use the Pi GPIO JTAG adapter. UART is
   independently wired; FPGA application behavior is unavailable during reload.
5. Isolate, return JTAG to idle, restore SPI6 pin ownership, select application
   mode, then enable. Negotiate the protocol/version before sending work.

A mode switch must never generate a stray TCK edge or clock an application
transaction. GPIO/driver failures must leave the link isolated. Sensor
acquisition remains available without the FPGA or this control expander.

## Implementation sequence and acceptance evidence

1. **Circuit:** implement the six connections, switching/isolation, I2C control,
   pulls and decoupling in Atopile. Remove J85-J89 and their unused fanout.
   Preserve power/ground fixtures, UART, reset and geophone analog placement.
   Replace the 155-breakout requirement with a complete module-contact audit
   distinguishing required connections, power/ground and deliberate no-connects.
2. **PCB and mechanics:** rebuild the netlist, route the link over uninterrupted
   return planes, remove ribbon stubs and guide/spacer assets from the active
   assembly, check four straight supports, and retain the 85 x 56 mm outline.
   Do not reduce the existing layer count without a separate routing assessment.
   Regenerate schematic, BOM, native routing snapshot, 3D renders and UI model.
3. **Host and FPGA:** add exclusive SPI6/JTAG ownership and recovery, a bounded
   framed FIFO protocol (length, version, sequence, CRC and backpressure), and
   SPI slave RTL with asynchronous FIFO/clock-domain constraints. UART remains
   a diagnostic/fallback channel. Quad mode must be capability-negotiated; do
   not add an enabled quad device-tree property to the Pi 4 SPI controller.
4. **Verify:** check independent connector fixtures; ERC/DRC and unrouted nets;
   clean route replay; powered/unpowered and switching cases; SPI/JTAG/UART
   conflict tests; malformed frames, FIFO overflow, aborts and reset recovery;
   FPGA timing/CDC and quad turnaround contention; sensor regression tests;
   updated stack fit and UI model. Run the project checker and portable unit/full
   lab. Existing ribbon-only collision assertions are retired with their parts,
   while sensor, geophone, cooler and support checks remain.

Start physical SPI bring-up at a conservative clock and increase only with
measured round-trip integrity under simultaneous acquisition. Test long bursts,
power cycling and both boards powered independently. Simulation cannot certify
the final link timing, supply behavior or sensor noise under FPGA activity.

## Planning validation

The pin-budget review checks the live Atopile J1 connections, the Pi deployment
overlay, the vendor I/O and module/carrier fixtures, and the clock pad in the
vendor schematic. It establishes pin availability and a conflict-free reservation,
not electrical implementation, routing completion or transport performance.
