# Trenz FPGA integration

Current scope is TE0712-03-81I36-A pin/connectivity qualification and, when needed,
small GPIO/UART test bitstreams. Sensor software must not depend on an accelerator
bitstream. See the [sensor development plan](../../docs/sensor-development-plan.md)
and the
[carrier design and connector mapping](../../docs/trenz-hat.md).

The carrier exposes 155 available Trenz GPIOs on J85-J89 while preserving
existing interfaces. Follow the [GPIO contract](../../docs/trenz-gpio-breakout.csv)
and [electrical limits](../../docs/trenz-hat.md#gpio-expansion). Package-ball
constraints and small test bitstreams are still needed; derive them from the
exact module schematic rather than guessing from carrier pad numbers.

Coldfoot RTL/bitstream integration is deferred. Keep its authoritative RTL in its
own repository and pin an explicit
revision when integration begins. Do not copy a second mutable RTL tree here.
An existing bitstream for a different FPGA package is not a Trenz port.

The Trenz bitstream port and on-board qualification are pending.
