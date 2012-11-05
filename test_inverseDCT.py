# coding:utf-8
# test_inverseDCT.py 2012.11.5
import inverseDCT
import forwardDCT
import unittest
import copy

class my_idct(inverseDCT.inverseDCT_aan):
    def outputBLOCK(self, mcu, block, values):
        self.result = copy.deepcopy(values)

class my_idct_f(inverseDCT.inverseDCT_aan_f):
    def outputBLOCK(self, mcu, block, values):
        self.result = copy.deepcopy(values)

def print_dump64(s, title=None):
    if title:
        print title
    for i,v in enumerate(s):
        print "%+5d," % v,
        if i%8 == 7:
            print

def diff64(s1, s2):
    r = 0
    for i in range(64):
        a = abs(s1[i]-s2[i])
        if a > r:
            r = a
    return r

def convzz(s):
    r = []
    for i in inverseDCT.zigzag:
        r.append(s[i])
    return r

class TestIDCT(unittest.TestCase):
    def setUp(self):
        self.idct = my_idct()
        self.idct_f = my_idct_f()
        self.dct_f = forwardDCT.forwardDCT_f()

    def test_diff64(self):
        s1 = range(64)
        s2 = range(64)
        r = diff64(s1, s2)
        self.assertEqual(r, 0)
        s1 = [1]*64
        s2 = [3]*64
        r = diff64(s1, s2)
        self.assertEqual(r, 2)

    def test_0x64(self):
        s = [0]*64
        self.dct_f.calc(1,2,s)
        for scan,c in enumerate(self.dct_f.result):
            self.idct.inputBLOCK(1, 2, scan, c)
            self.idct_f.inputBLOCK(3, 4, scan, c)
        self.assertEqual(self.idct.result, self.idct_f.result)

    def test_127x64(self):
        s = [127]*64
        self.dct_f.calc(1,2,s)
        for scan,c in enumerate(self.dct_f.result):
            self.idct.inputBLOCK(1, 2, scan, c)
            self.idct_f.inputBLOCK(3, 4, scan, c)
        r = diff64(self.idct.result, self.idct_f.result)
        self.assertTrue(r <= 2)

    def test_m128x64(self):
        s = [-128]*64
        self.dct_f.calc(1,2,s)
        for scan,c in enumerate(self.dct_f.result):
            self.idct.inputBLOCK(1, 2, scan, c)
            self.idct_f.inputBLOCK(3, 4, scan, c)
        r = diff64(self.idct.result, self.idct_f.result)
        self.assertTrue(r <= 2)

    def test_range(self):
        s = range(-128,127,4)
        #print_dump64(s, u"画素値")

        self.dct_f.calc(1,2,s)
        #print_dump64(self.dct_f.result, u"DCT変換")

        s2 = convzz(self.dct_f.result)
        #print_dump64(s2, u"ジグザグ変換")

        for scan,c in enumerate(s2):
            self.idct.inputBLOCK(1, 2, scan, c)
            self.idct_f.inputBLOCK(3, 4, scan, c)
        #print_dump64(self.idct.result, u"逆DCT変換")
        
        r = diff64(self.idct.result, self.idct_f.result)
        #print u"計算誤差: %d" % r
        self.assertTrue(r <= 2)

        s3 = []
        for c in self.idct.result:
            s3.append(c)
        #print_dump64(s3)
 
        r = diff64(s, s3)
        #print u"計算誤差: %d" % r
        self.assertTrue(r <= 2)

    def test_random(self):
        import random
        s = []
        for n in range(64):
            s.append(random.randint(-128, 127))
        print_dump64(s, u"ランダムな画像")

        self.dct_f.calc(1,2,s)
        #print_dump64(self.dct_f.result, u"DCT変換")

        s2 = convzz(self.dct_f.result)
        #print_dump64(s2, u"ジグザグ変換")

        for scan,c in enumerate(s2):
            self.idct.inputBLOCK(1, 2, scan, c)
            self.idct_f.inputBLOCK(3, 4, scan, c)
        print_dump64(self.idct.result, u"逆DCT変換")
        
        r = diff64(self.idct.result, self.idct_f.result)
        print u"計算誤差: %d" % r
        self.assertTrue(r <= 3)

        s3 = []
        for c in self.idct.result:
            s3.append(c)
        print_dump64(s3, u"復元した画像")
 
        r = diff64(s, s3)
        print u"計算誤差: %d" % r
        self.assertTrue(r <= 3)

class TestIDCT(unittest.TestCase):
    def setUp(self):
        self.dct_f = forwardDCT.forwardDCT_f()
        self.dct_i = forwardDCT.forwardDCT_i()
        self.idct = my_idct()
        self.idct_f = my_idct_f()

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
        for i in range(64):
            a = abs(self.dct_f.result[i]-self.dct_i.result[i])
            self.assertTrue(a < 3)

    def test_m128x64(self):
        s = [-128]*64
        self.dct_f.calc(1,2,s)
        self.dct_i.calc(3,4,s)
        self.assertEqual(self.dct_f.result, self.dct_i.result)

