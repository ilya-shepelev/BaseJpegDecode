# coding:utf-8
# forwardDCT.py 2012.11.1
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

class forwardDCT_f(): # 浮動小数点演算版
    def __init__(self):
        self.N = 8
        self.result = [0]*64

    def calc(self, mcu, block, s):
        for v in range(self.N):
            cv = 1.0
            if v == 0:
                cv /= math.sqrt(2)
            for u in range(self.N):
                cu = 1.0
                if u == 0:
                    cu /= math.sqrt(2)
                sum = 0.0
                for y in range(self.N):
                    for x in range(self.N):
                        cosxu = math.cos((x*2+1)*u*math.pi/(self.N*2))
                        cosyv = math.cos((y*2+1)*v*math.pi/(self.N*2))
                        sum += s[y*8+x] * cosxu * cosyv
                self.result[v*8+u] = int(round(cu * cv * sum / 4.0))

class forwardDCT_i(): # 整数演算版
    def __init__(self, callback=None):
        self.N=8
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
        for v in range(self.N):
            for u in range(self.N):
                sum = 0
                for y in range(self.N):
                    for x in range(self.N):
                        t1 = self._cucv[(u,v)] * s[y*8+x] * self._cosxu[(x, u)] * self._cosxu[(y, v)]
                        CHECK32bit(t1)
                        t1 /= self._cosxuQ
                        t1 /= self._cosxuQ
                        sum += t1
                self.result[v*8+u] = sum * self._cucv[(u,v)] / self._cucvQ / 4

import unittest
class TestDCT(unittest.TestCase):
    def setup(self):
        self.dct_f = forwardDCT_f()
        self.dct_i = forwardDCT_i()

    def test_0x64(self):
        s = [0]*64
        self.dct_f.calc(1,2,s)
        self.dct_i.calc(3,4,s)
        self.assertEqual(self.dct_f.result, self.dct_i.result)
        self.assertEqual(self.dct_f.result, s)

    def test_127x64(self):
        s = [127]*64
        self.dct_f.calc(1,2,s)
        self.dct_i.calc(3,4,s)
        self.assertEqual(self.dct_f.result, self.dct_i.result)

    def test_m128x64(self):
        s = [-128]*64
        self.dct_f.calc(1,2,s)
        self.dct_i.calc(3,4,s)
        self.assertEqual(self.dct_f.result, self.dct_i.result)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse
    import profile
    import inspect
    from inverseDCT import inverseDCT

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
            print "const uint8_t cucv[] = {"
            for i,v in enumerate(idct._cucv):
                print "%d," % v,
                if i%8 == 7:
                    print
            print "};"

            print "const int8_t cosxu[] = {"
            for i,v in enumerate(idct._cosxu):
                print "%3d," % v,
                if i%8 == 7:
                    print
            print "};"


    dct_f = forwardDCT_f()
    dct_i = forwardDCT_i()
    s = [-128]*64

    def dump64(s):
        for i,v in enumerate(s):
            print "%+5d" % v,
            if i%8 == 7:
                print

    def loop(dct):
        for mcu in range(10):
            dct.calc(mcu, 0, s)
            if mcu == 0:
                dump64(dct.result)

    class ProfileAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            profile.run("loop(dct_f)")
            profile.run("loop(dct_i)")

    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='*')
    parser.add_argument('--table', nargs='*', action=TableAction)
    parser.add_argument('--profile', nargs='*', action=ProfileAction)
