"""Exclusive DAQHAT-01 mode control and bounded SPI packet framing.

Sensor acquisition never imports or initializes this module. The switch is
isolated until explicitly enabled. Quad mode is not advertised on Pi 4.
"""
from contextlib import contextmanager
import struct
import time
import zlib

ADDRESS = 0x20
MAX_PAYLOAD = 192
HEADER = struct.Struct('<4sBBHH')
MAX_FRAME = HEADER.size + MAX_PAYLOAD + 4


def encode(payload, sequence, operation=1):
    if not isinstance(payload, bytes) or len(payload)>MAX_PAYLOAD:
        raise ValueError('FPGA payload must be bytes, at most 192 bytes')
    if not 0<=sequence<=65535 or not 1<=operation<=255:
        raise ValueError('FPGA sequence/operation outside range')
    data=HEADER.pack(b'SSFP',1,operation,sequence,len(payload))+payload
    return data+struct.pack('<I',zlib.crc32(data))


def decode(frame):
    if not HEADER.size+4<=len(frame)<=MAX_FRAME:
        raise ValueError('FPGA frame length')
    magic,version,operation,sequence,length=HEADER.unpack_from(frame)
    if magic!=b'SSFP' or version!=1 or not operation:
        raise ValueError('FPGA protocol identity/version')
    if length>MAX_PAYLOAD or len(frame)!=HEADER.size+length+4:
        raise ValueError('FPGA payload length')
    if zlib.crc32(frame[:-4])!=struct.unpack_from('<I',frame,len(frame)-4)[0]:
        raise ValueError('FPGA frame CRC')
    return operation,sequence,frame[HEADER.size:-4]


class ModeControl:
    """TCA9534: P0=JTAG select, P1=request enable; P2-P7 stay inputs.

    Bus implements Linux I2C.exchange. Owner implements release/acquire for
    'spi'/'jtag' and prepares safe pin directions while the switch is isolated.
    A caller holds an OS lock across the entire context and all transfers.
    """
    def __init__(self,bus,owner,arm,sleep=time.sleep):
        self.bus,self.owner,self.arm,self.sleep=bus,owner,arm,sleep
        self.mode=None
        self.faulted=False
        self.arm.enabled(False)
        self.write(1,0)  # Output latch BEFORE direction: reset latch is 0xFF.
        self.write(3,0xFC)
        self.write(2,0)
        self.check(1,0);self.check(3,0xFC)

    def write(self,register,value):
        self.bus.exchange(ADDRESS,bytes((register,value)),0)

    def check(self,register,expected):
        if self.bus.exchange(ADDRESS,bytes((register,)),1)!=bytes((expected,)):
            raise OSError('FPGA switch register readback mismatch')

    def isolate(self):
        try:
            self.arm.enabled(False)  # Independent of the I2C bus.
        finally:
            # Still use the second disable path if the GPIO operation failed.
            self.write(1,1 if self.mode=='jtag' else 0)
            self.check(1,1 if self.mode=='jtag' else 0)
        self.sleep(.001)  # Conservative settling interval; not a clock delay.

    @contextmanager
    def active(self,mode):
        if mode not in ('spi','jtag'):raise ValueError('SPI or JTAG only; native quad unavailable')
        if self.mode is not None or self.faulted:raise RuntimeError('FPGA link busy or faulted')
        acquired=False
        try:
            self.isolate()
            self.owner.acquire(mode)
            acquired=True
            self.mode=mode
            select=int(mode=='jtag')
            self.write(1,select);self.check(1,select)
            self.sleep(.001)
            self.write(1,select|2);self.check(1,select|2)
            self.arm.enabled(True)
            yield
        finally:
            try:
                self.isolate()
            except BaseException:
                # The independent arm was lowered before the failed I2C access.
                # Retain ownership on error; explicit reinitialization is required.
                self.faulted=True
                raise
            finally:
                if acquired and not self.faulted:
                    try:self.owner.release(mode)
                    except BaseException:
                        self.faulted=True
                        raise
                if not self.faulted:self.mode=None


class Packets:
    """SPI mode-0 packet mailbox client; protocol documented in fpga-host-link.md.

    No retries of uncertain writes: the caller must renegotiate/reset the peer.
    Transport ownership and mode enable are the caller's responsibility.
    """
    def __init__(self,spi,hz=1_000_000,clock=time.monotonic,sleep=time.sleep):
        if not 1_000<=hz<=1_000_000:raise ValueError('Unqualified SPI clock; bring-up limited to 1 MHz')
        self.spi,self.hz,self.clock,self.sleep=spi,hz,clock,sleep

    def transfer(self,data):
        self.sleep(.001)  # CS-high recovery between mailbox transactions.
        response=self.spi.transfer(data,mode=0,hz=self.hz)
        if len(response)!=len(data):raise OSError('Short FPGA SPI transaction')
        return response

    def status(self):
        raw=self.transfer(bytes(9))[1:]
        if raw[:4]!=b'SSFP' or raw[4]!=1:raise OSError('Unconfigured FPGA or unsupported protocol')
        if raw[5]!=0:raise OSError('Unsupported FPGA capabilities')
        if raw[7]:raise OSError(f'FPGA transport error {raw[7]}')
        if raw[6] not in (0,1,2):raise OSError('Invalid FPGA mailbox flags')
        return raw[6]

    def exchange(self,payload,sequence,timeout=1.0):
        if not 0<timeout<=10:raise ValueError('Bounded timeout required')
        frame=encode(payload,sequence)
        if self.status()!=1:raise BlockingIOError('FPGA mailbox is not empty; do not overwrite results')
        self.transfer(b'\x01'+frame)
        deadline=self.clock()+timeout
        for _ in range(1000):
            if self.clock()>=deadline:raise TimeoutError('FPGA processing timeout; write outcome unknown')
            status=self.status()
            if self.clock()>=deadline:raise TimeoutError('FPGA processing timeout; write outcome unknown')
            if status&2:break
            self.sleep(.001)
        else:raise TimeoutError('FPGA polling limit')
        raw=self.transfer(b'\x02'+bytes(MAX_FRAME))[1:]
        length=struct.unpack_from('<H',raw,8)[0]
        if length>MAX_PAYLOAD:raise ValueError('FPGA result bound')
        operation,received,result=decode(raw[:HEADER.size+length+4])
        if operation!=1 or received!=sequence:raise ValueError('Stale or mismatched FPGA result')
        self.transfer(b'\x03'+struct.pack('<H',sequence))
        if self.status()!=1:raise OSError('FPGA acknowledgement not confirmed; do not repeat submit')
        return result
