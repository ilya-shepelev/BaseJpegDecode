# BaseJpegDecode.py 2013/1/27
# coding:utf-8
import abc
import logging
from collections import Counter

class BitPattern:
    def __init__(self, data=0, size=0):
        self.data = data
        self.size = size

    def clear(self):
        self.data = 0
        self.size = 0

    def put(self, c, size=8):
        self.data <<= size
        self.data |= c
        self.size += size
        if self.size > 32:
            logging.error("%08X %d" % (self.data, self.size))
            raise ValueError('over flow 32bit')

    def peek(self, size):
        return self.data >> (self.size-size)

    def get(self, size):
        r = self.peek(size)
        self.size -= size
        self.data &= (1<<self.size)-1
        return r

    def match(self, b):
        if b.size > self.size:
            return False
        return self.peek(b.size) == b.peek(b.size)

class Huff:
    def __init__(self, run, value_size, code):
        self.run = run
        self.value_size = value_size
        self.code = code

class HuffmanDecode(object):
    def __init__(self):
        self._ht = {}

    def _ht_clear(self, tc, th):
        self._ht[(tc,th)] = []

    def _ht_append(self, tc, th, huff):
        self._ht[(tc,th)].append(huff)

    def inputDHT(self, c, pos, size):
        if pos == 0:
            self._buf = []
        self._buf.append(c)
        if pos < (size-1):
            return
        pos = 0
        while pos < len(self._buf):
            uc = self._buf[pos]
            pos += 1
            tc = uc >> 4
            th = uc & 0x0f
            logging.info("DHT: Tc=%d Th=%d" %(tc, th))
            self._ht_clear(tc, th)
            l_pos = pos
            pos += 16
            code = 0x0000
            for i in range(16):
                l = self._buf[l_pos + i]
                for k in range(l):
                    value = self._buf[pos]
                    run = value >> 4;
                    value_size = value & 0x0f
                    h = Huff(run, value_size, BitPattern(code, i+1))
                    self._ht_append(tc, th, h)
                    pos += 1
                    code += 1
                code <<= 1

    def Lookup(self, tc, th, bitpat):
        for h in self._ht[(tc,th)]:
            if h.code.size > bitpat.size:
                return None
            if bitpat.match(h.code):
                return h
        logging.error("(%d,%d)%08X %d" % (tc, th, bitpat.data, bitpat.size))
        raise ValueError('Huffman decode error')
        return None

    def getValue(self, huff, bitpat):
        if huff.value_size == 0:
            return 0
        value = bitpat.get(huff.value_size)
        if value & (1<<(huff.value_size-1)):
            return value
        value -= (1<<huff.value_size)-1
        return value

MARK_SOF0 = 0xc0
MARK_DHT  = 0xc4
MARK_RST0 = 0xd0
MARK_RST7 = 0xd7
MARK_SOI  = 0xd8
MARK_EOI  = 0xd9
MARK_SOS  = 0xda
MARK_DQT  = 0xdb
MARK_DRI  = 0xdd
MARK_APP  = 0xe0

SEQ_INIT     = 0
SEQ_SOI      = 1
SEQ_FRAME    = 2
SEQ_MARK     = 3
SEQ_SEG_LEN  = 4
SEQ_SEG_LEN2 = 5
SEQ_SEG_BODY = 6
SEQ_SOS      = 7
SEQ_SOS2     = 8

class BaseJpegDecode(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._hd = HuffmanDecode()
        self.qt = {}
        self.clear()

    def clear(self):
        self._seq = SEQ_INIT

    @abc.abstractmethod
    def outputDC(self, mcu, block, value):
        pass

    @abc.abstractmethod
    def outputAC(self, mcu, block, scan, value):
        pass

    @abc.abstractmethod
    def outputMARK(self, c):
        pass

    def _restart(self):
        self._block = 0
        self._scan = 0
        self._pre_DC_value = [0]*3
        self._bitpat = BitPattern()
        self._huff = None

    def _inputScan(self, c):
        self._bitpat.put(c)
        while self._bitpat.size > 0:
            if self._scan == 0:
                tc = 0 # DC
            else:
                tc = 1 # AC
            if self._block < self._yblock: # 2 or 4
                th = 0 # Y
            else:
                th = 1 # CbCr
            if self._huff == None:
                self._huff = self._hd.Lookup(tc, th, self._bitpat)
                if self._huff == None:
                    break
                self._bitpat.get(self._huff.code.size) # skip code
            if self._huff.value_size > self._bitpat.size:
                break
            value = self._hd.getValue(self._huff, self._bitpat)
            if self._scan == 0: #DC
                sc = 0 # Y
                if self._block == self._yblock:
                    sc = 1 # Cb
                elif self._block == (self._yblock+1):
                    sc = 2 # Cr
                value += self._pre_DC_value[sc]
                self.outputDC(self._mcu, self._block, value)
                self._pre_DC_value[sc] = value
                self._scan += 1
            else: # AC
                if self._huff.run == 0 and self._huff.value_size == 0: # EOB
                    self.outputAC(self._mcu, self._block, 63, 0)
                    self._scan = 64
                else:
                    for i in range(self._huff.run):
                        #self.outputAC(self._mcu, self._block, self._scan, 0)
                        self._scan += 1
                    self.outputAC(self._mcu, self._block, self._scan, value)
                    self._scan += 1
                if self._scan >= 64:
                    self._scan = 0
                    self._block += 1
                    if self._block >= (self._yblock+2): # 4 or 6
                        self._block = 0
                        self._mcu += 1
            self._huff = None

    def _inputDQT(self, c, pos, size):
        if pos == 0 or pos == 65:
            self._tq = c
            self.qt[self._tq] = []
        else:
            self.qt[self._tq].append(c)
        if pos == (size-1): # last
            for tq in range(2):
                if tq in self.qt:
                    s = ",".join(["%d" % c for c in self.qt[tq]])
                    logging.info("DQT(%d): %s" % (tq, s))

    def _inputSOF(self, c, pos, len):
        if pos == 1:
            self.height = c<<8
        elif pos == 2:
            self.height += c
        elif pos == 3:
            self.width = c<<8
        elif pos == 4:
            self.width += c
        elif pos == 7:
            if c == 0x22:
                self._yblock = 4
            elif c == 0x21:
                self._yblock = 2
            else:
                raise ValueError('SOF error')
        if pos == (len-1):
            logging.info("SOF: width=%d height=%d yblock=%d" % (self.width, self.height, self._yblock))

    def _inputSOS(self, c, pos, len):
        if pos == 0:
            self._buf = []
        self._buf.append(c)
        if pos == (len-1): #last
            s = ",".join(["%02X" % c for c in self._buf])
            logging.info("SOS: "+ s)

    def input(self, c):
        if c < 0 or c > 0xff:
            raise ValueError('input error')
        if self._seq == SEQ_INIT:
            if c == 0xff:
                self._seq = SEQ_SOI
        elif self._seq == SEQ_SOI:
            if c == MARK_SOI:
                self.outputMARK(c)
                self._seq = SEQ_FRAME
            else:
                self._seq = SEQ_INIT
        elif self._seq == SEQ_FRAME:
            if c == 0xff:
                self._seq = SEQ_MARK
            else:
                self._seq = SEQ_INIT
        elif self._seq == SEQ_MARK:
            self.outputMARK(c)
            if c == MARK_SOI:
                self._seq = SEQ_FRAME
            elif c == MARK_EOI or c == 0x00:
                self._seq = SEQ_INIT
            else:
                self._mark = c
                self._seq = SEQ_SEG_LEN
        elif self._seq == SEQ_SEG_LEN:
            self._seg_len = c << 8
            self._seq = SEQ_SEG_LEN2
        elif self._seq == SEQ_SEG_LEN2:
            self._seg_len += c
            self._seg_len -= 2
            self._seg_pos = 0
            self._seq = SEQ_SEG_BODY
        elif self._seq == SEQ_SEG_BODY:
            if self._mark == MARK_SOS: # SOS
                self._inputSOS(c, self._seg_pos, self._seg_len)
            elif self._mark == MARK_SOF0: # SOF0
                self._inputSOF(c, self._seg_pos, self._seg_len)
            elif self._mark == MARK_DQT: # DQT
                self._inputDQT(c, self._seg_pos, self._seg_len)
            elif self._mark == MARK_DHT: # DHT
                self._hd.inputDHT(c, self._seg_pos, self._seg_len)
            else:
                pass
            self._seg_pos += 1
            if self._seg_pos < self._seg_len:
                return
            if self._mark == MARK_SOS: # SOS
                self._mcu = 0
                self._restart()
                self._seq = SEQ_SOS
            else:
                self._seq = SEQ_FRAME
        elif self._seq == SEQ_SOS:
            if c == 0xff:
                self._seq = SEQ_SOS2
            else:
                self._inputScan(c)
        elif self._seq == SEQ_SOS2:
            if c == 0x00:
                self._inputScan(0xff)
                self._seq = SEQ_SOS
            elif c >= MARK_RST0 and c <= MARK_RST7: # RSTx
                self._restart()
                self._seq = SEQ_SOS
            elif c == MARK_EOI: # EOI
                self.outputMARK(c)
                self._seq = SEQ_INIT
            else:
                self.outputMARK(c)
                self._seq = SEQ_INIT
        else:
            pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    class DemoJpeg(BaseJpegDecode):
        def __init__(self):
            super(DemoJpeg, self).__init__()

        def outputDC(self, mcu, block, value):
            if self._yblock == 2:
                if block <= 1:
                    print "%3d" % value,
                    if block == 1:
                        if (mcu % (self.width/16)) == (self.width/16)-1:
                            print ""
                return
            if block == 0:
                self._value = 0
            if block <= 3:
                self._value += (value+512)
                if block == 3:
                    print("%02X" % (self._value/16)),
                    if (mcu % (self.width/16)) == (self.width/16)-1:
                        print ""

        def outputAC(self, mcu, block, scan, value):
            pass

        def outputMARK(self, c):
            print("MARK: %02X" % c)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='*')
    args = parser.parse_args()

    jpeg = DemoJpeg()

    for filename in args.infiles:
        with open(filename, "rb") as f:
            data = f.read()
        print("%s %d" % (filename, len(data)))
        jpeg.clear()
        for c in data:
            jpeg.input(ord(c))
