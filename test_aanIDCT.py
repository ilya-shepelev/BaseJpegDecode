# coding:utf-8
# test_aanIDCT.py 2012.11.5
#
import math
import unittest
import aanIDCT

DCTSIZE = 8
DCTSIZE2 = 64

class prototypeIDCT:
    def conv(self, output, input):
        for y in range(DCTSIZE):
            for x in range(DCTSIZE):
                sum = 0.0
                for v in range(DCTSIZE):
                    cv = 1.0
                    if v == 0:
                        cv /= math.sqrt(2)
                    for u in range(DCTSIZE):
                        cu = 1.0
                        if u == 0:
                            cu /= math.sqrt(2)
                        vu = v*8+u
                        cosxu = math.cos((x*2+1)*u*math.pi/(DCTSIZE*2))
                        cosyv = math.cos((y*2+1)*v*math.pi/(DCTSIZE*2))
                        sum += cu * cv * input[vu] * cosxu * cosyv
                output[y*8+x] = int(round(sum / (DCTSIZE/2)))

class Test_aanIDCT(unittest.TestCase):
    def setUp(self):
        self.idct = aanIDCT.aanIDCT()
        #self.idct = aanIDCT.aanIDCT_f()
        self.idct_i = aanIDCT.aanIDCT()
        self.idct_f = aanIDCT.aanIDCT_f()
        self.prototype = prototypeIDCT()

    def test_SCALEUP(self):
        self.assertEqual(self.idct_i.SCALEUP(1,0), 1)
        self.assertEqual(self.idct_i.SCALEUP(2,1), 4)
        self.assertEqual(self.idct_i.DESCALE(256,1), 128)
        
    def test_aanscales(self):
        #self.print_dump(self.idct_i.aanscales, fmt="%5.4f")
        self.assertEqual(self.idct_i.aanscales[0], 16384);
        self.assertEqual(self.idct_i.aanscales[63], 1247);
        #self.print_dump(self.idct_f.aanscales, fmt="%5.4f")
        self.assertEqual(self.idct_f.aanscales[0], 1.0/8)
        self.assertEqualFloat(self.idct_f.aanscales[4], 1.0/8, fmt="%5.4f")

    def test_all_zero(self):
        s = [0]*64
        d = range(DCTSIZE2)
        #self.print_dump(s)
        self.idct.conv(d,s)
        #self.print_dump(d)
        for i in range(DCTSIZE2):
            self.assertEqual(d[i], 0)

    def test_dc(self):
        s = [0]*64
        s[0] = 512
        d = range(DCTSIZE2)
        #self.print_dump(s)
        self.idct.conv(d,s)
        #self.print_dump(d)
        for i in range(DCTSIZE2):
            self.assertEqual(d[i], s[0]/8)

    def row0_data(self, data):
        s = [0]*DCTSIZE2
        s[0:len(data)] = data
        d = range(DCTSIZE2)
        #self.print_dump(s, "%+5d")
        self.idct.conv(d,s)
        #self.print_dump(d, "%+4d")
        for x in range(DCTSIZE):
            for pos in range(DCTSIZE, DCTSIZE2, DCTSIZE):
                self.assertEqual(d[x], d[pos+x])

    def column0_data(self, data):
        s = [0]*DCTSIZE2
        for i,c in enumerate(data):
            s[i*DCTSIZE] = c
        d = range(DCTSIZE2)
        #self.print_dump(s, "%+5d")
        self.idct.conv(d, s)
        #self.print_dump(d, "%+4d")
        for pos in range(0, DCTSIZE2, 8):
            for x in range(DCTSIZE):
                self.assertEqual(d[pos+0], d[pos+x])

    def test_only_row0(self):
        self.row0_data([-512,64])
        self.row0_data([-512,64,-32])
        self.row0_data([1023,0,0,0])
        self.row0_data([1023,-512,0,0])
        self.row0_data([1,2,3,4,5,6,7,8])

    def test_only_column0(self):
        self.column0_data([512])
        self.column0_data([256])
        self.column0_data([256,256])
        self.column0_data([255,255])
        self.column0_data([-256,-256])
        self.column0_data([1,2,3,4,5,6,7,8])

    def comp_prototype(self, data, verbose=False, allow=2):
        s1 = [0]*DCTSIZE2
        s2 = [0]*DCTSIZE2
        for i,c in enumerate(data):
            s1[i] = c
            s2[i] = c
        d1 = range(DCTSIZE2)
        d2 = range(DCTSIZE2)
        if verbose:
            self.print_dump(s1, "%+5d")
        self.idct.conv(d1, s1)
        self.prototype.conv(d2, s2)
        if verbose:
            self.print_dump(d1, "%+4d")
            self.print_dump(d2, "%+4d")
        for i in range(DCTSIZE2):
            #self.assertEqual(d1[i], d2[i])
            self.assertTrue(abs(d1[i]-d2[i]) <= allow)

    def test_comp_prototype1(self):
        self.comp_prototype([0])
        self.comp_prototype([256])
        self.comp_prototype([512])
        self.comp_prototype([1023])
        self.comp_prototype([-1024])
        self.comp_prototype([64,0,0,0,0,0,0,0,64])

    def test_comp_prototype2(self):
        self.comp_prototype([64,64])
        self.comp_prototype([64,32,0,0,0,0,0,0,64])

    def test_comp_prototype3(self):
        import random
        for loop in range(10):
            s = []
            for n in range(DCTSIZE2):
                s.append(random.randint(-128, 127))
            #self.comp_prototype(s, True)
            self.comp_prototype(s)

    def assertEqualFloat(self, f1, f2, fmt="%5.4f"):
        s1 = fmt % f1
        s2 = fmt % f2
        self.assertEqual(s1, s2)

    def print_dump(self, s, fmt="%5.4f"):
        for i,c in enumerate(s):
            print fmt % c,
            if i%8==7:
                print

if __name__ == "__main__":
    unittest.main()
