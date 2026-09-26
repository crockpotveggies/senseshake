"""Bind only DAQHAT-01's five explicitly identified userspace SPI nodes; no unbinding."""
from pathlib import Path
import argparse
import json


def inventory(root=Path('/sys/bus/spi')):
    devices = []
    for i in range(5):
        device = root / 'devices' / f'spi0.{i}'
        expected = b'groundlark,' + (b'lsm6dso-userspace' if i < 4 else b'scl3300-userspace')
        if (device / 'of_node/compatible').read_bytes().rstrip(b'\0') != expected:
            raise ValueError(f'{device.name}: not the DAQHAT-01 userspace device')
        driver = (device / 'driver').resolve().name if (device / 'driver').exists() else None
        if driver not in (None, 'spidev'): raise ValueError(f'{device.name}: owned by {driver}; refusing to detach it')
        devices.append((device, driver))
    return devices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    devices = inventory()  # Check every node before any mutation.
    if args.apply:
        for device, driver in devices:
            if driver == 'spidev': continue
            (device / 'driver_override').write_text('spidev\n')
            Path('/sys/bus/spi/drivers/spidev/bind').write_text(device.name + '\n')
    print(json.dumps({'mode':'applied' if args.apply else 'check-only', 'devices':[p.name for p, _ in devices]}))


if __name__ == '__main__': main()
