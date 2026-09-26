import struct
import unittest
from groundlark.fpga_link import ModeControl,Packets,encode,decode,MAX_FRAME


class Arm:
    def __init__(self):self.on=False;self.history=[]
    def enabled(self,value):self.on=value;self.history.append(value)


class Bus:
    def __init__(self,arm):self.r=[0,255,0,255];self.log=[];self.fail=False;self.arm=arm
    def exchange(self,address,write,count):
        assert address==0x20
        if self.fail:raise OSError('bus disconnected')
        self.log.append((bytes(write),count))
        if len(write)==2:
            assert not self.arm.on, 'Registers changed while host drivers enabled'
            self.r[write[0]]=write[1]
            return b''
        return bytes([self.r[write[0]]])


class Owner:
    def __init__(self,arm):self.arm=arm;self.events=[];self.fail=False
    def acquire(self,mode):
        assert not self.arm.on
        self.events.append(('acquire',mode))
        if self.fail:raise OSError('driver busy')
    def release(self,mode):
        assert not self.arm.on
        self.events.append(('release',mode))


class Peer:
    """Independent byte-level test peer; no frame helper shared with producer."""
    def __init__(self):self.frame=None;self.corrupt=False;self.slow=False;self.count=0
    def transfer(self,data,mode,hz):
        assert mode==0 and hz<=1_000_000
        self.count+=1
        if data[0]==0:
            status=2 if self.frame is not None else 1
            if self.slow:status=0
            return b'\x00SSFP\x01\x00'+bytes((status,0))
        if data[0]==1:
            if self.frame is not None:raise AssertionError('overwritten result')
            self.frame=data[1:]
            assert self.frame[:6]==b'SSFP\x01\x01'
            assert int.from_bytes(self.frame[8:10],'little')+14==len(self.frame)
            crc=0xffffffff
            for byte in self.frame[:-4]:
                crc^=byte
                for _ in range(8):crc=(crc>>1)^(0xedb88320 if crc&1 else 0)
            assert (crc^0xffffffff)==int.from_bytes(self.frame[-4:],'little')
            return bytes(len(data))
        if data[0]==2:
            result=self.frame
            if self.corrupt:result=result[:-1]+bytes([result[-1]^1])
            return b'\x00'+result+bytes(MAX_FRAME-len(result))
        if data[0]==3:
            assert data[1:3]==self.frame[6:8]
            self.frame=None
            return bytes(3)
        raise AssertionError('unknown command')


class LinkTests(unittest.TestCase):
    def make(self):
        arm=Arm();bus=Bus(arm);owner=Owner(arm)
        return ModeControl(bus,owner,arm,lambda _:None),bus,owner,arm

    def test_latch_written_before_direction(self):
        control,bus,owner,arm=self.make()
        self.assertEqual(bus.log[:2],[(b'\x01\x00',0),(b'\x03\xfc',0)])
        self.assertFalse(arm.on)

    def test_program_and_spi_are_exclusive_and_return_isolated(self):
        control,bus,owner,arm=self.make()
        for mode,register in [('jtag',3),('spi',2)]:
            with control.active(mode):
                self.assertTrue(arm.on);self.assertEqual(bus.r[1],register)
                with self.assertRaises(RuntimeError):
                    with control.active('spi'):pass
            self.assertFalse(arm.on)
            self.assertEqual(bus.r[1]&2,0)
        self.assertEqual(owner.events,[('acquire','jtag'),('release','jtag'),('acquire','spi'),('release','spi')])

    def test_transport_error_disconnects_before_releasing_pins(self):
        control,bus,owner,arm=self.make()
        with self.assertRaisesRegex(ValueError,'test'):
            with control.active('spi'):raise ValueError('test')
        self.assertFalse(arm.on);self.assertEqual(owner.events[-1],('release','spi'))

    def test_lost_i2c_still_has_independent_hardware_disarm(self):
        control,bus,owner,arm=self.make()
        with self.assertRaises(OSError):
            with control.active('jtag'):bus.fail=True
        self.assertFalse(arm.on)
        self.assertTrue(control.faulted)
        self.assertNotIn(('release','jtag'),owner.events)
        with self.assertRaises(RuntimeError):
            with control.active('spi'):pass

    def test_failed_pin_ownership_never_enables_link(self):
        control,bus,owner,arm=self.make();owner.fail=True
        with self.assertRaises(OSError):
            with control.active('jtag'):pass
        self.assertFalse(any(arm.history))

    def test_native_quad_rejected(self):
        control,*_=self.make()
        with self.assertRaises(ValueError):
            with control.active('quad'):pass

    def test_packet_boundaries_and_independent_crc(self):
        peer=Peer();client=Packets(peer)
        for n in (0,1,191,192):
            payload=bytes(range(n))
            self.assertEqual(client.exchange(payload,65535),payload)
            self.assertIsNone(peer.frame)
        with self.assertRaises(ValueError):encode(bytes(193),0)
        with self.assertRaises(ValueError):encode(b'',65536)

    def test_corrupt_or_stale_result_is_not_acknowledged(self):
        peer=Peer();peer.corrupt=True
        with self.assertRaisesRegex(ValueError,'CRC'):Packets(peer).exchange(b'123456789',4)
        self.assertIsNotNone(peer.frame)
        with self.assertRaises(BlockingIOError):Packets(peer).exchange(b'next',5)

    def test_invalid_identity_length_and_crc_rejected(self):
        frame=encode(b'test',3)
        for i in range(len(frame)):
            damaged=bytearray(frame);damaged[i]^=1
            with self.assertRaises(ValueError):decode(damaged)
        for damaged in (frame[:-1],frame+b'\x00',b'',bytes(MAX_FRAME+1)):
            with self.assertRaises(ValueError):decode(damaged)

    def test_timeout_is_bounded_even_with_stalled_clock(self):
        class Slow(Peer):
            def transfer(self,data,**kwargs):
                result=super().transfer(data,**kwargs)
                if data[0]==1:self.slow=True
                return result
        peer=Slow()
        with self.assertRaises(TimeoutError):Packets(peer,clock=lambda:0,sleep=lambda _:None).exchange(b'x',0)
        self.assertLessEqual(peer.count,1002)

    def test_unqualified_clock_rejected(self):
        with self.assertRaises(ValueError):Packets(Peer(),hz=50_000_000)

    def test_gpio_disable_failure_still_uses_i2c_disable(self):
        from unittest.mock import patch
        control,bus,owner,arm=self.make()
        with self.assertRaisesRegex(OSError,'GPIO'):
            with control.active('spi'):
                arm.on=False  # Model readback unknown; bus fixture only checks sequencing.
                with patch.object(arm,'enabled',side_effect=OSError('GPIO failed')):
                    control.isolate()
        self.assertEqual(bus.r[1]&2,0)

    def test_linux_owner_rebinds_after_partial_gpio_failure(self):
        from groundlark.fpga_linux import Owner
        from unittest.mock import patch,Mock
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            owner=Owner.__new__(Owner);owner.chip='/dev/gpiochip0'
            owner.controller=Path(tmp)/'spi6';owner.controller.mkdir()
            owner.driver=Path(tmp)/'driver';owner.driver.mkdir()
            owner.detached=False;owner.handles=[]
            first=Mock()
            with patch('groundlark.fpga_linux.Lines',side_effect=[first,OSError('busy')]):
                with self.assertRaises(OSError):owner.acquire('jtag')
            first.close.assert_called_once()
            self.assertEqual((owner.driver/'bind').read_text(),'spi6')
            self.assertFalse(owner.detached)

    def test_invalid_mailbox_flags_rejected(self):
        class Invalid(Peer):
            def transfer(self,data,**kwargs):return b'\x00SSFP\x01\x00\x03\x00'
        with self.assertRaises(OSError):Packets(Invalid()).status()

    def test_binding_rejects_missing_cs_timing_before_driver_change(self):
        from groundlark.fpga_linux import Owner
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            owner=Owner.__new__(Owner);owner.controller=Path(tmp)
            device=owner.controller/'spi_master/spi6/spi6.0'
            node=device/'of_node';node.mkdir(parents=True)
            (node/'compatible').write_bytes(b'groundlark,fpga-userspace\0')
            for prop in ('setup','hold','inactive'):
                (node/f'spi-cs-{prop}-delay-ns').write_bytes((0).to_bytes(4,'big'))
            with self.assertRaisesRegex(RuntimeError,'timing'):owner.spi_path()
            self.assertFalse((device/'driver_override').exists())
            (node/'compatible').write_bytes(b'wrong-device\0')
            with self.assertRaisesRegex(RuntimeError,'overlay'):owner.spi_path()

    def test_each_spi_transaction_has_recovery_gap(self):
        from unittest.mock import Mock
        gap=Mock();peer=Peer();client=Packets(peer,sleep=gap)
        self.assertEqual(client.exchange(b'gap',4),b'gap')
        self.assertEqual(gap.call_count,peer.count)
        gap.assert_called_with(.001)

    def test_result_at_or_after_deadline_is_not_read_or_acknowledged(self):
        for elapsed in (1.0, 1.001):
            peer=Peer()
            ticks=iter((0,0,elapsed))
            with self.assertRaises(TimeoutError):
                Packets(peer,clock=lambda:next(ticks),sleep=lambda _:None).exchange(b'late',4)
            self.assertEqual(peer.count,3)
            self.assertIsNotNone(peer.frame)

    def test_lost_acknowledgement_is_not_reported_as_success(self):
        class LostAck(Peer):
            def transfer(self,data,**kwargs):
                if data[0]==3:return bytes(len(data))
                return super().transfer(data,**kwargs)
        peer=LostAck()
        with self.assertRaisesRegex(OSError,'acknowledgement'):
            Packets(peer,sleep=lambda _:None).exchange(b'retained',9)
        self.assertIsNotNone(peer.frame)

    def test_every_transfer_fault_stops_without_retry(self):
        # Status, submit, ready poll, result read, ACK, ACK confirmation.
        for failed in range(1,7):
            for failure in ('short','io'):
                class Fault(Peer):
                    def transfer(self,data,**kwargs):
                        if self.count+1==failed:
                            self.count+=1
                            if failure=='io':raise OSError('injected')
                            return bytes(len(data)-1)
                        return super().transfer(data,**kwargs)
                peer=Fault()
                with self.assertRaises(OSError):
                    Packets(peer,sleep=lambda _:None).exchange(b'fault',5)
                self.assertEqual(peer.count,failed)

    def test_stale_sequence_and_operation_are_not_acknowledged(self):
        for operation,sequence in ((1,10),(2,9)):
            class Stale(Peer):
                def transfer(self,data,**kwargs):
                    result=super().transfer(data,**kwargs)
                    if data[0]==1:self.frame=encode(b'stale',sequence,operation)
                    return result
            peer=Stale()
            with self.assertRaisesRegex(ValueError,'mismatched'):
                Packets(peer,sleep=lambda _:None).exchange(b'original',9)
            self.assertIsNotNone(peer.frame)

    def test_register_readback_mismatch_never_arms(self):
        from unittest.mock import patch
        control,bus,owner,arm=self.make()
        original=bus.exchange
        def mismatch(address,write,count):
            result=original(address,write,count)
            return b'\xff' if count else result
        with patch.object(bus,'exchange',side_effect=mismatch):
            with self.assertRaisesRegex(OSError,'readback'):
                with control.active('spi'):self.fail('enabled despite mismatch')
        self.assertFalse(any(arm.history))
        self.assertTrue(control.faulted)

    def test_driver_restore_failure_latches_faulted_ownership(self):
        from unittest.mock import patch
        control,bus,owner,arm=self.make()
        with patch.object(owner,'release',side_effect=OSError('rebind failed')):
            with self.assertRaisesRegex(OSError,'rebind'):
                with control.active('jtag'):pass
        self.assertFalse(arm.on)
        self.assertEqual(bus.r[1],1)
        self.assertTrue(control.faulted)
        with self.assertRaises(RuntimeError):
            with control.active('spi'):pass

    def test_sigterm_unwinds_and_restores_handler(self):
        import importlib.util
        from pathlib import Path
        import signal
        path=Path(__file__).resolve().parents[1]/'tools/fpga.py'
        spec=importlib.util.spec_from_file_location('fpga_cli',path)
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        previous=signal.getsignal(signal.SIGTERM)
        control,bus,owner,arm=self.make()
        with self.assertRaises(SystemExit) as error:
            with cli.termination_cleanup(),control.active('jtag'):
                signal.raise_signal(signal.SIGTERM)
        self.assertEqual(error.exception.code,128+signal.SIGTERM)
        self.assertEqual(signal.getsignal(signal.SIGTERM),previous)
        self.assertFalse(arm.on)
        self.assertEqual(bus.r[1],1)
        self.assertEqual(owner.events[-1],('release','jtag'))


if __name__=='__main__':unittest.main()
