# Trenz FPGA integration

T1-LINK reserves six SPI/QSPI signals and retains UART/reset. Four data-link
wires switch to dedicated JTAG for programming directly from the Pi. See the
[host-link guide](../../docs/fpga-host-link.md) and
[pin contract](../../docs/trenz-gpio-breakout.csv).

The initial Pi 4 transport is ordinary SPI6, with DQ2/DQ3 unused. Quad needs a
separate host engine and reviewed slave RTL. Keep sensor acquisition independent
of FPGA configuration. Coldfoot integration remains deferred; an existing Nexys
Video bitstream is not a Trenz port.

`rtl/t1_link.sv` is a single-clock 50 MHz SPI echo mailbox with length/CRC/sequence
checks and one-frame backpressure. Run `python3 sw/fpga/test.py` with the pinned
Icarus installation, or use the full/software lab profile. `build.tcl` implements
it for XC7A200T-FBG484-1 in Vivado; run from ignored `.local/` storage. The
[recorded implementation evidence](verification/result.json) includes timing,
CDC, DRC and source hashes. Physical Pi/Trenz programming remains untested.
