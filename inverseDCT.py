# coding:utf-8
# inverseDCT.py 2012.10.30
import abc
import math
import logging

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

class inverseDCT(object): # 整数演算版・最適化・イベント駆動
    __metaclass__ = abc.ABCMeta

    def __init__(self, callback=None):
        self.N = 8
        self.callback = callback
        self.result = [0]*64

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

    @abc.abstractmethod
    def outputBLOCK(self, mcu, block, values):
        pass

    def inputBLOCK(self, mcu, block, scan, value):
        if scan == 0:
            self._sum = [0]*64

        if value != 0:
            uv = zigzag[scan]
            u = uv % 8
            v = uv / 8
            for y in range(self.N):
                for x in range(self.N):
                    t1 = self._cucv[uv] * value * self._cosxu[x*8+u] * self._cosxu[y*8+v]
                    t1 /= self._cosxuQ
                    t1 /= self._cosxuQ
                    t2 = self._sum[y*8+x]
                    t3 = t2 + t1
                    self._sum[y*8+x] = t3

        if scan == 63:
            result = [0]*64
            for i,c in enumerate(self._sum):
                result[i] = adjust(c / self._cucvQ)
            self.outputBLOCK(mcu, block, result)

class inverseDCT_f(): # 浮動小数点演算版
    def __init__(self, callback=None):
        self.N = 8
        self.callback = callback
        self.result = [0]*64

    def calc(self, mcu, block, s):
        for y in range(self.N):
            for x in range(self.N):
                sum = 0.0
                for v in range(self.N):
                    cv = 1.0
                    if v == 0:
                        cv /= math.sqrt(2)
                    for u in range(self.N):
                        cu = 1.0
                        if u == 0:
                            cu /= math.sqrt(2)
                        vu = v*8+u
                        cosxu = math.cos((x*2+1)*u*math.pi/(self.N*2))
                        cosyv = math.cos((y*2+1)*v*math.pi/(self.N*2))
                        sum += cu * cv * s[vu] * cosxu * cosyv
                sum /= (self.N/2)
                self.result[y*8+x] = adjust(sum)
        if self.callback:
            self.callback(mcu, block, self.result)

    def input(self, mcu, block, scan, value):
        uv = zigzag[scan]
        if uv == 0:
            self._s = [0]*64
        self._s[uv] = value
        if uv == 63:
            self.calc(mcu, block, self._s)

class inverseDCT_i(): # 整数演算版
    def __init__(self, callback=None):
        self.N=8
        self.callback = callback
        self.result = [0]*64

        self._cosxuQ = 32
        self._cosxu = {}
        for x in range(self.N):
            for u in range(self.N):
                value = math.cos((x*2+1)*u*math.pi/(self.N*2))
                self._cosxu[(x,u)] = int(round(value * self._cosxuQ))

        self._cucvQ = 32
        self._cucv = {}
        for v in range(self.N):
            for u in range(self.N):
                value = 1.0/(self.N/2)
                if v == 0 and u == 0:
                    value /= 2.0
                elif v == 0 or u == 0:
                    value /= math.sqrt(2)
                self._cucv[(v,u)] = int(round(value * self._cucvQ))

    def calc(self, mcu, block, s):
        for y in range(self.N):
            for x in range(self.N):
                sum = 0
                for v in range(self.N):
                    for u in range(self.N):
                        vu = v*8+u
                        t1 = self._cucv[(u,v)] * s[vu] * self._cosxu[(x, u)] * self._cosxu[(y, v)]
                        CHECK32bit(t1)
                        t1 /= self._cosxuQ
                        t1 /= self._cosxuQ
                        sum += t1
                        CHECK16bit(sum)
                value = adjust(sum / self._cucvQ)
                self.result[y*8+x] = value
        if self.callback:
            self.callback(mcu, block, self.result)

    def input(self, mcu, block, scan, value):
        uv = zigzag[scan]
        if uv == 0:
            self._s = [0]*64
        self._s[uv] = value
        if uv == 63:
            self.calc(mcu, block, self._s)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse
    import profile
    import inspect

    class my_idct(inverseDCT):
        def outputBLOCK(self, mcu, block, values):
            if mcu != 0:
                return
            for i,v in enumerate(values):
                print "%02X" % v,
                if i%8 == 7:
                    print

    class TableAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            idct = my_idct()
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


    idct = my_idct()
    s = [-127]*64
    s[0] = -1011

    def loop(idct):
        for i in range(10):
            for scan, value in enumerate(s):
                idct.inputBLOCK(i, 0, scan, value)

    class ProfileAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            profile.run("loop(idct)")

    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='*')
    parser.add_argument('--table', nargs='*', action=TableAction)
    parser.add_argument('--profile', nargs='*', action=ProfileAction)
    args = parser.parse_args()

