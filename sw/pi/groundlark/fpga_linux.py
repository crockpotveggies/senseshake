"""Pi 4 ownership adapter. Optional hardware path, not used by acquisition."""
import ctypes as c
import os
from pathlib import Path
from .linux_io import GPIORequest,ioctl


class Lines:
    def __init__(self,chip,offsets,values=None):
        import re
        if not re.fullmatch(r'/dev/gpiochip\d+',chip):raise ValueError('Explicit GPIO chip required')
        self.fd=None
        fd=os.open(chip,os.O_RDONLY|os.O_CLOEXEC)
        try:
            req=GPIORequest();req.lines=len(offsets);req.flags=1 if values is None else 2
            req.consumer=b'groundlark-fpga'
            for i,offset in enumerate(offsets):
                req.offsets[i]=offset
                req.values[i]=0 if values is None else values[i]
            data=bytearray(bytes(req))
            ioctl(fd,(3<<30)|(c.sizeof(req)<<16)|(0xb4<<8)|3,data,True)
            self.fd=GPIORequest.from_buffer_copy(data).fd
        finally:os.close(fd)

    def set(self,values):ioctl(self.fd,0xc040b409,bytes(values)+bytes(64-len(values)))

    def close(self):
        if self.fd is not None:os.close(self.fd);self.fd=None


class Arm:
    """Existing BCM25 UART enable also hard-disarms the switched data/JTAG link."""
    def __init__(self,chip):self.line=Lines(chip,[25],[0])
    def enabled(self,value):self.line.set([int(bool(value))])
    def close(self):
        try:self.enabled(False)
        finally:self.line.close()


class Owner:
    def __init__(self,chip):
        self.chip=chip;self.handles=[];self.detached=False
        compatible=Path('/proc/device-tree/compatible').read_bytes()
        if b'brcm,bcm2711\0' not in compatible:raise RuntimeError('This adapter implements the Pi 4 pin mapping only')
        alias=Path('/proc/device-tree/aliases/spi6').read_bytes().rstrip(b'\0').decode()
        node=Path('/sys/firmware/devicetree/base'+alias).resolve(strict=True)
        candidates=[p for p in Path('/sys/bus/platform/devices').iterdir()
                    if (p/'of_node').exists() and (p/'of_node').resolve()==node]
        if len(candidates)!=1:raise RuntimeError('Cannot identify exactly one SPI6 controller')
        self.controller=candidates[0]
        self.driver=(self.controller/'driver').resolve(strict=True)
        if self.driver.name!='spi-bcm2835':raise RuntimeError('Unexpected SPI6 driver')

    def acquire(self,mode):
        if mode not in ('spi','jtag'):raise ValueError('SPI or JTAG ownership required')
        if mode=='spi':
            if not (self.controller/'driver').exists():raise RuntimeError('SPI6 driver is not bound')
            self.handles.append(Lines(self.chip,[16,12]))
            return
        try:
            (self.driver/'unbind').write_text(self.controller.name)
            self.detached=True
            self.handles.append(Lines(self.chip,[21,16,20,18],[0,1,0,1]))
            self.handles.append(Lines(self.chip,[19,12]))
        except BaseException:
            self.release(mode)
            raise

    def release(self,mode):
        for handle in reversed(self.handles):handle.close()
        self.handles=[]
        if self.detached:
            (self.driver/'bind').write_text(self.controller.name)
            self.detached=False

    def spi_path(self):
        paths=list(self.controller.glob('spi_master/spi*/spi*.0'))
        if len(paths)!=1:raise RuntimeError('Expected one SPI6 chip-select-zero device')
        device=paths[0]
        node=device/'of_node'
        if b'groundlark,fpga-userspace' not in (node/'compatible').read_bytes().split(b'\0'):
            raise RuntimeError('SPI6 device is not the DAQHAT-01 overlay')
        for prop in ('setup','hold','inactive'):
            if int.from_bytes((node/f'spi-cs-{prop}-delay-ns').read_bytes(),'big')<1000:
                raise RuntimeError('SPI6 CS timing is below the loopback requirement')
        driver=device/'driver'
        if not driver.exists():
            (device/'driver_override').write_text('spidev')
            Path('/sys/bus/spi/drivers/spidev/bind').write_text(device.name)
        elif driver.resolve().name!='spidev':raise RuntimeError('SPI6 device is owned by another driver')
        return '/dev/spidev'+device.name.removeprefix('spi')
