"""Настоящий Z80-код адаптера; модель заменяет только электрический SPI-интерфейс."""
from collections import deque
import unittest
from harness import Driver,Disk


class Card:
    def __init__(self,disk,kind='sdhc'):
        self.disk,self.kind=disk,kind
        self.selected,self.idle=False,True
        self.packet,self.reply=[],deque()
        self.commands,self.pending_write=[],None
        self.write_data=None
        self.reject_write=False
        self.fail_write=None
        self.lost_token=False

    def output(self,port,value):
        if port&255==0x77:
            self.selected=value in (1,11)
            if not self.selected:
                self.packet=[]
                self.reply.clear()
            return
        assert port&255==0x57,hex(port)
        if not self.selected:
            return
        if self.pending_write is not None:
            if self.write_data is None:
                if value==0xFE:
                    self.write_data=[]
                return
            self.write_data.append(value)
            if len(self.write_data)==514:
                rejected=self.reject_write or (self.fail_write and
                    self.fail_write(self.pending_write,bytes(self.write_data[:512])))
                if not rejected:
                    self.disk.write(self.pending_write,bytes(self.write_data[:512]))
                self.reply.extend([0x0D if rejected else 5,0,0,0xFF])
                self.pending_write,self.write_data=None,None
            return
        if not self.packet:
            if value&0xC0==0x40:
                self.packet=[value]
            return
        self.packet.append(value)
        if len(self.packet)==6:
            packet=self.packet
            self.packet=[]
            self.command(packet[0]&63,int.from_bytes(bytes(packet[1:5]),'big'),packet[5])

    def input(self,port):
        assert port&255==0x57,hex(port)
        return self.reply.popleft() if self.reply and self.selected else 0xFF

    def command(self,cmd,arg,crc):
        self.commands.append((cmd,arg))
        if cmd==0:
            assert crc==0x95
            self.idle=True
            self.reply.append(1)
        elif cmd==8:
            assert arg==0x1AA and crc==0x87
            self.reply.extend([1,0,0,1,0xAA] if self.kind=='sdhc' else [5])
        elif cmd==55:
            self.reply.append(5 if self.kind=='mmc' else int(self.idle))
        elif cmd in (1,41):
            assert (cmd==1)==(self.kind=='mmc')
            assert arg==(0x40000000 if self.kind=='sdhc' else 0)
            self.idle=False
            self.reply.append(0)
        elif cmd==58:
            self.reply.extend([0,0xC0,0xFF,0x80,0])
        elif cmd==16:
            assert arg==512
            self.reply.append(0)
        elif cmd in (17,24):
            assert not self.idle
            if self.kind!='sdhc':
                assert arg%512==0
                arg//=512
            self.reply.append(0)
            if cmd==17:
                if not self.lost_token:
                    self.reply.extend([0xFF,0xFE])
                    self.reply.extend(self.disk.read(arg))
                    self.reply.extend([0xFF,0xFF])
            else:
                self.pending_write=arg
        else:
            raise AssertionError(('Unexpected command',cmd,arg))


class ZController:
    """Порт #57 возвращает прошлый байт и запускает следующий SPI-обмен.

    И IN, и OUT дают восемь тактов; при IN на MOSI отправляется FF.
    Контракт сверён с TZc::Rd/Wr в исходнике Unreal (zc.cpp).
    """
    def __init__(self, card):
        self.card = card
        self.latched = 0xFF

    def output(self, port, value):
        if port & 255 == 0x57:
            self.latched = self.card.input(port)
        self.card.output(port, value)

    def input(self, port):
        value = self.latched
        self.output(port, 0xFF)
        return value


class SdzcTests(unittest.TestCase):
    def test_sd_and_mmc_filesystem(self):
        for kind in ('sdhc','sdsc','mmc'):
            disk=Disk(partition=2048)
            card=Card(disk,kind)
            h=Driver(disk,native=ZController(card))
            self.assertEqual(h.create('file.bin'),(0,True,False),kind)
            data=bytes(i%251 for i in range(1200))
            self.assertEqual(h.append(data),(0,True,False),kind)
            self.assertEqual(disk.contents('file.bin'),data)
            self.assertEqual(h.call(35),(0,True,False))
            self.assertFalse(card.selected)
            disk.assert_mirrors()

    def test_missing_token_and_rejected_write(self):
        disk=Disk()
        card=Card(disk)
        h=Driver(disk,native=ZController(card))
        self.assertEqual(h.create('file.bin'),(0,True,False))
        card.reject_write=True
        self.assertNotEqual(h.append(b'data')[0],0)
        self.assertFalse(card.selected)
        self.assertEqual(disk.contents('file.bin'),b'')
        card.lost_token=True
        self.assertTrue(h.find('file.bin')[2])
        self.assertFalse(card.selected)


if __name__=='__main__':
    unittest.main()
