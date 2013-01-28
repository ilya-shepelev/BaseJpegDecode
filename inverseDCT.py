# inverseDCT.py 2013/1/27
# coding:utf-8
import abc
import math
import logging
import aanIDCT

zigzag = [ 0,
           1, 8,
          16, 9, 2,
           3,10,17,24,
          32,25,18,11, 4,
          5,12,19,26,33,40,
          48,41,34,27,20,13,6,
           7,14,21,28,35,42,49,56,
          57,50,43,36,29,22,15,
          23,30,37,44,51,58,
          59,52,45,38,31,
          39,46,53,60,
          61,54,47,
          55,62,
          63]

def adjust(value):
    value += 128
    if value < 0:
        return 0
    elif value > 255:
        return 255
    return int(value)


def CHECK8bit(data):
    if data > 127:
        raise ValueError("8bit over flow")
    elif data <-128:
        raise ValueError("8bit over flow")

def CHECK16bit(data):
    if data > (2<<14-1):
        raise ValueError("16bit over flow")
    elif data <-(2<<14):
        raise ValueError("16bit over flow")

def CHECK32bit(data):
    if data > (2<<30-1):
        raise ValueError("32bit over flow")
    elif data <-(2<<30):
        raise ValueError("32bit over flow")

class inverseDCT_aan(object): # AAN整数値演算版
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._result = [0]*64
        self.aan = aanIDCT.aanIDCT()

    @abc.abstractmethod
    def outputBLOCK(self, mcu, block, values):
        pass

    def inputBLOCK(self, mcu, block, scan, value):
        uv = zigzag[scan]
        if uv == 0:
            self._s = [0]*64
        self._s[uv] = value
        if uv == 63:
            self.aan.conv(self._result, self._s)
            for i in range(64):
                CHECK8bit(self._result[i])
            self.outputBLOCK(mcu, block, self._result)

class inverseDCT_aan_f(object): # AAN浮動小数点演算版
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._result = [0]*64
        self.aan = aanIDCT.aanIDCT_f()

    @abc.abstractmethod
    def outputBLOCK(self, mcu, block, values):
        pass

    def inputBLOCK(self, mcu, block, scan, value):
        uv = zigzag[scan]
        if uv == 0:
            self._s = [0]*64
        self._s[uv] = value
        if uv == 63:
            self.aan.conv(self._result, self._s)
            for i in range(64):
                CHECK8bit(self._result[i])
            self.outputBLOCK(mcu, block, self._result)

class inverseDCT_tbl(object): # データ駆動,省RAMメモリ
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.N = 8

        self._cosxuQ = 32
        self._cosxu = [0]*64
        for x in range(self.N):
            for u in range(self.N):
                value = math.cos((x*2+1)*u*math.pi/(self.N*2))
                self._cosxu[x*8+u] = int(round(value * self._cosxuQ))

        self._cucvQ = 32
        self._cucv = [0]*64
        for v in range(self.N):
            for u in range(self.N):
                value = 1.0/(self.N/2)
                if v == 0 and u == 0:
                    value /= 2.0
                elif v == 0 or u == 0:
                    value /= math.sqrt(2)
                self._cucv[v*8+u] = int(round(value * self._cucvQ))

        self._idct_tableQ = 16
        self._idct_table = [0]*64*64
        for scan in range(64):
            uv = zigzag[scan]
            v = uv/8
            u = uv%8
            cv = 1.0
            if v == 0:
                cv /= math.sqrt(2)
            cu = 1.0
            if u == 0:
                cu /= math.sqrt(2)
            for y in range(8):
                for x in range(8):
                    value = cu * cv * math.cos((x*2+1)*u*math.pi/16) * math.cos((y*2+1)*v*math.pi/16)
                    value /= 4.0
                    t = int(round(value * self._idct_tableQ * self._cucvQ))
                    CHECK8bit(t)
                    self._idct_table[scan*64+y*8+x] = t

    @abc.abstractmethod
    def outputBLOCK(self, mcu, block, values):
        pass

    def inputBLOCK(self, mcu, block, scan, value):
        if scan == 0:
            t = value * self._cucvQ / 8
            self._sum = [t]*64
            return

        if value != 0:
            for xy in range(64):
                t = self._idct_table[scan*64+xy] * value / self._idct_tableQ
                self._sum[xy] += t

        if scan == 63:
            for i in range(64):
                self._sum[i] /= self._cucvQ
            self.outputBLOCK(mcu, block, self._sum)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse
    import profile
    import inspect

    class my_idct_aan(inverseDCT_aan):
        def outputBLOCK(self, mcu, block, values):
            if mcu != 0:
                return
            for i,v in enumerate(values):
                print "%02X" % v,
                if i%8 == 7:
                    print

    class my_idct_aan_f(inverseDCT_aan_f):
        def outputBLOCK(self, mcu, block, values):
            if mcu != 0:
                return
            for i,v in enumerate(values):
                print "%+5d" % v,
                if i%8 == 7:
                    print

    class my_idct_tbl(inverseDCT_tbl):
        def outputBLOCK(self, mcu, block, values):
            if mcu != 0:
                return
            for i,v in enumerate(values):
                print "%02X" % v,
                if i%8 == 7:
                    print

    class TableAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            idct = my_idct_tbl()
            print "const int cucv[] = {"
            for i,v in enumerate(idct._cucv):
                print "%d," % v,
                if i%8 == 7:
                    print
            print "};"

            print "const int cosxu[] = {"
            for i,v in enumerate(idct._cosxu):
                print "%3d," % v,
                if i%8 == 7:
                    print
            print "};"

            print "const int8_t idct_table[] = {"
            for uv in range(64):
                print "// %2d" % uv
                for i in range(64):
                    print "%4d," % idct._idct_table[uv*64+i],
                    if i%8 == 7:
                        print
            print "};"

    idct_aan = my_idct_aan()
    idct_aan_f = my_idct_aan_f()
    s = [-127]*64
    s[0] = 1023

    def loop(idct):
        for i in range(10):
            for scan, value in enumerate(s):
                idct.inputBLOCK(i, 0, scan, value)

    class ProfileAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            profile.run("loop(idct_aan)")
            profile.run("loop(idct_aan_f)")

    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='*')
    parser.add_argument('--table', nargs='*', action=TableAction)
    parser.add_argument('--profile', nargs='*', action=ProfileAction)
    args = parser.parse_args()

