# coding:utf-8
# aanIDCT.py 2012.11.4
#
# libjpeg(jpeg-8d)jidctfst.cからの移植
#
import abc
import math
import logging
import unittest

DCTSIZE = 8
DCTSIZE2 = 64

FIX_1_082392200 = 1.082392200
FIX_1_414213562 = 1.414213562
FIX_1_847759065 = 1.847759065
FIX_2_613125930 = 2.613125930

def DEQUANTIZE(coef, quantval):
    return coef * quantval

def MULTIPLY(a, b):
    return a * b

class aanIDCT_f: # 浮動小数点演算版
    def __init__(self):
        self.aanscales = [0]*DCTSIZE2
        for v in range(DCTSIZE):
            vs = math.cos(v*math.pi/16) * math.sqrt(2)
            if v == 0:
                vs = 1.0
            for u in range(DCTSIZE):
                us = math.cos(u*math.pi/16) * math.sqrt(2)
                if u == 0:
                    us = 1.0
                self.aanscales[v*DCTSIZE+u] = vs * us / 8

    def conv(self, output, input):
        quant = self.aanscales
        ws = [0]*DCTSIZE2
        for pos in range(DCTSIZE):
            if input[pos+DCTSIZE*1] == 0 and input[pos+DCTSIZE*2] == 0 and \
               input[pos+DCTSIZE*3] == 0 and input[pos+DCTSIZE*4] == 0 and \
               input[pos+DCTSIZE*5] == 0 and input[pos+DCTSIZE*6] == 0 and \
               input[pos+DCTSIZE*7] == 0:
                dcval = DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
                for y in range(DCTSIZE):
                    ws[pos+DCTSIZE*y] = dcval
                continue

            # Even part
            tmp0 = DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
            tmp1 = DEQUANTIZE(input[pos+DCTSIZE*2], quant[pos+DCTSIZE*2])
            tmp2 = DEQUANTIZE(input[pos+DCTSIZE*4], quant[pos+DCTSIZE*4])
            tmp3 = DEQUANTIZE(input[pos+DCTSIZE*6], quant[pos+DCTSIZE*6])

            tmp10 = tmp0 + tmp2     # phase 3
            tmp11 = tmp0 - tmp2

            tmp13 = tmp1 + tmp3     # phases 5-3
            tmp12 = MULTIPLY(tmp1 - tmp3, FIX_1_414213562) - tmp13  # 2*c4

            tmp0 = tmp10 + tmp13    # phase 2
            tmp3 = tmp10 - tmp13
            tmp1 = tmp11 + tmp12
            tmp2 = tmp11 - tmp12

            # Odd part
            tmp4 = DEQUANTIZE(input[pos+DCTSIZE*1], quant[pos+DCTSIZE*1])
            tmp5 = DEQUANTIZE(input[pos+DCTSIZE*3], quant[pos+DCTSIZE*3])
            tmp6 = DEQUANTIZE(input[pos+DCTSIZE*5], quant[pos+DCTSIZE*5])
            tmp7 = DEQUANTIZE(input[pos+DCTSIZE*7], quant[pos+DCTSIZE*7])

            z13 = tmp6 + tmp5       # phase 6
            z10 = tmp6 - tmp5
            z11 = tmp4 + tmp7
            z12 = tmp4 - tmp7

            tmp7 = z11 + z13        # phase 5
            tmp11 = MULTIPLY(z11 - z13, FIX_1_414213562)    # 2*c4

            z5 = MULTIPLY(z10 + z12, FIX_1_847759065)       # 2*c2
            #tmp10 = MULTIPLY(z12, FIX_1_082392200) - z5    # 2*(c2-c6)
            tmp10 = MULTIPLY(z12, - FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = MULTIPLY(z10, - FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
            #tmp4 = tmp10 + tmp5
            tmp4 = tmp10 - tmp5

            ws[pos+DCTSIZE*0] = tmp0 + tmp7
            ws[pos+DCTSIZE*7] = tmp0 - tmp7
            ws[pos+DCTSIZE*1] = tmp1 + tmp6
            ws[pos+DCTSIZE*6] = tmp1 - tmp6
            ws[pos+DCTSIZE*2] = tmp2 + tmp5
            ws[pos+DCTSIZE*5] = tmp2 - tmp5
            ws[pos+DCTSIZE*3] = tmp3 + tmp4
            ws[pos+DCTSIZE*4] = tmp3 - tmp4

        for pos in range(0, DCTSIZE2, DCTSIZE):
            if ws[pos+1] == 0 and ws[pos+2] == 0 and ws[pos+3] == 0 and \
               ws[pos+4] == 0 and ws[pos+5] == 0 and ws[pos+6] == 0 and \
               ws[pos+7] == 0:
                dcval = ws[pos+0]
                for x in range(DCTSIZE):
                    output[pos+x] = int(dcval)
                continue

            # Even part
            tmp10 = ws[pos+0] + ws[pos+4]
            tmp11 = ws[pos+0] - ws[pos+4]

            tmp13 = ws[pos+2] + ws[pos+6]
            tmp12 = MULTIPLY(ws[pos+2] - ws[pos+6], FIX_1_414213562) - tmp13

            tmp0 = tmp10 + tmp13
            tmp3 = tmp10 - tmp13
            tmp1 = tmp11 + tmp12
            tmp2 = tmp11 - tmp12

            # Odd part
            z13 = ws[pos+5] + ws[pos+3]
            z10 = ws[pos+5] - ws[pos+3]
            z11 = ws[pos+1] + ws[pos+7]
            z12 = ws[pos+1] - ws[pos+7]

            tmp7 = z11 + z13        # phase 5
            tmp11 = MULTIPLY(z11 - z13, FIX_1_414213562)    # 2*c4

            z5 = MULTIPLY(z10 + z12, FIX_1_847759065)       # 2*c2
            #tmp10 = MULTIPLY(z12, FIX_1_082392200) - z5    # 2*(c2-c6)
            tmp10 = MULTIPLY(z12, - FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = MULTIPLY(z10, - FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
            #tmp4 = tmp10 + tmp5
            tmp4 = tmp10 - tmp5

            output[pos+0] = int(tmp0 + tmp7)
            output[pos+7] = int(tmp0 - tmp7)
            output[pos+1] = int(tmp1 + tmp6)
            output[pos+6] = int(tmp1 - tmp6)
            output[pos+2] = int(tmp2 + tmp5)
            output[pos+5] = int(tmp2 - tmp5)
            output[pos+3] = int(tmp3 + tmp4)
            output[pos+4] = int(tmp3 - tmp4)

# libjpeg(jpeg-8d)jidctfst.cの未修正の浮動小数点演算版
class aanIDCT_jidctfst: 
    def __init__(self):
        self.aanscales = [0]*DCTSIZE2
        for v in range(DCTSIZE):
            vs = math.cos(v*math.pi/16) * math.sqrt(2)
            if v == 0:
                vs = 1.0
            for u in range(DCTSIZE):
                us = math.cos(u*math.pi/16) * math.sqrt(2)
                if u == 0:
                    us = 1.0
                self.aanscales[v*DCTSIZE+u] = vs * us / 8

    def conv(self, output, input):
        quant = self.aanscales
        ws = [0]*DCTSIZE2
        for pos in range(DCTSIZE):
            if input[pos+DCTSIZE*1] == 0 and input[pos+DCTSIZE*2] == 0 and \
               input[pos+DCTSIZE*3] == 0 and input[pos+DCTSIZE*4] == 0 and \
               input[pos+DCTSIZE*5] == 0 and input[pos+DCTSIZE*6] == 0 and \
               input[pos+DCTSIZE*7] == 0:
                dcval = DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
                for y in range(DCTSIZE):
                    ws[pos+DCTSIZE*y] = dcval
                continue

            # Even part
            tmp0 = DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
            tmp1 = DEQUANTIZE(input[pos+DCTSIZE*2], quant[pos+DCTSIZE*2])
            tmp2 = DEQUANTIZE(input[pos+DCTSIZE*4], quant[pos+DCTSIZE*4])
            tmp3 = DEQUANTIZE(input[pos+DCTSIZE*6], quant[pos+DCTSIZE*6])

            tmp10 = tmp0 + tmp2     # phase 3
            tmp11 = tmp0 - tmp2

            tmp13 = tmp1 + tmp3     # phases 5-3
            tmp12 = MULTIPLY(tmp1 - tmp3, FIX_1_414213562) - tmp13  # 2*c4

            tmp0 = tmp10 + tmp13    # phase 2
            tmp3 = tmp10 - tmp13
            tmp1 = tmp11 + tmp12
            tmp2 = tmp11 - tmp12

            # Odd part
            tmp4 = DEQUANTIZE(input[pos+DCTSIZE*1], quant[pos+DCTSIZE*1])
            tmp5 = DEQUANTIZE(input[pos+DCTSIZE*3], quant[pos+DCTSIZE*3])
            tmp6 = DEQUANTIZE(input[pos+DCTSIZE*5], quant[pos+DCTSIZE*5])
            tmp7 = DEQUANTIZE(input[pos+DCTSIZE*7], quant[pos+DCTSIZE*7])

            z13 = tmp6 + tmp5       # phase 6
            z10 = tmp6 - tmp5
            z11 = tmp4 + tmp7
            z12 = tmp4 - tmp7

            tmp7 = z11 + z13        # phase 5
            tmp11 = MULTIPLY(z11 - z13, FIX_1_414213562)    # 2*c4

            z5 = MULTIPLY(z10 + z12, FIX_1_847759065)       # 2*c2
            tmp10 = MULTIPLY(z12, FIX_1_082392200) - z5    # 2*(c2-c6)
            #tmp10 = MULTIPLY(z12, - FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = MULTIPLY(z10, - FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
            tmp4 = tmp10 + tmp5
            #tmp4 = tmp10 - tmp5

            ws[pos+DCTSIZE*0] = tmp0 + tmp7
            ws[pos+DCTSIZE*7] = tmp0 - tmp7
            ws[pos+DCTSIZE*1] = tmp1 + tmp6
            ws[pos+DCTSIZE*6] = tmp1 - tmp6
            ws[pos+DCTSIZE*2] = tmp2 + tmp5
            ws[pos+DCTSIZE*5] = tmp2 - tmp5
            ws[pos+DCTSIZE*3] = tmp3 + tmp4
            ws[pos+DCTSIZE*4] = tmp3 - tmp4

        for pos in range(0, DCTSIZE2, DCTSIZE):
            if ws[pos+1] == 0 and ws[pos+2] == 0 and ws[pos+3] == 0 and \
               ws[pos+4] == 0 and ws[pos+5] == 0 and ws[pos+6] == 0 and \
               ws[pos+7] == 0:
                dcval = ws[pos+0]
                for x in range(DCTSIZE):
                    output[pos+x] = int(dcval)
                continue

            # Even part
            tmp10 = ws[pos+0] + ws[pos+4]
            tmp11 = ws[pos+0] - ws[pos+4]

            tmp13 = ws[pos+2] + ws[pos+6]
            tmp12 = MULTIPLY(ws[pos+2] - ws[pos+6], FIX_1_414213562) - tmp13

            tmp0 = tmp10 + tmp13
            tmp3 = tmp10 - tmp13
            tmp1 = tmp11 + tmp12
            tmp2 = tmp11 - tmp12

            # Odd part
            z13 = ws[pos+5] + ws[pos+3]
            z10 = ws[pos+5] - ws[pos+3]
            z11 = ws[pos+1] + ws[pos+7]
            z12 = ws[pos+1] - ws[pos+7]

            tmp7 = z11 + z13        # phase 5
            tmp11 = MULTIPLY(z11 - z13, FIX_1_414213562)    # 2*c4

            z5 = MULTIPLY(z10 + z12, FIX_1_847759065)       # 2*c2
            tmp10 = MULTIPLY(z12, FIX_1_082392200) - z5    # 2*(c2-c6)
            #tmp10 = MULTIPLY(z12, - FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = MULTIPLY(z10, - FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
            tmp4 = tmp10 + tmp5
            #tmp4 = tmp10 - tmp5

            output[pos+0] = int(tmp0 + tmp7)
            output[pos+7] = int(tmp0 - tmp7)
            output[pos+1] = int(tmp1 + tmp6)
            output[pos+6] = int(tmp1 - tmp6)
            output[pos+2] = int(tmp2 + tmp5)
            output[pos+5] = int(tmp2 - tmp5)
            output[pos+3] = int(tmp3 + tmp4)
            output[pos+4] = int(tmp3 - tmp4)

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
        self.idct = aanIDCT_f()
        #self.idct = prototypeIDCT()
        self.prototype = prototypeIDCT()

    def test_aanscales(self):
        return
        #self.print_dump(self.idct.aanscales, fmt="%5.4f")
        self.assertEqual(self.idct.aanscales[0], 1.0/8)
        self.assertEqualFloat(self.idct.aanscales[4], 1.0/8, fmt="%5.4f")

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

    def comp_prototype(self, data, verbose=False):
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
            self.assertTrue(abs(d1[i]-d2[i])<=1)

    def test_comp_prototype(self):
        self.comp_prototype([0])
        self.comp_prototype([256])
        self.comp_prototype([512])
        self.comp_prototype([1023])
        self.comp_prototype([-1024])
        self.comp_prototype([64,0,0,0,0,0,0,0,64])
        self.comp_prototype([64,64])
        self.comp_prototype([64,32,0,0,0,0,0,0,64])
        import random
        for loop in range(10):
            s = []
            for n in range(DCTSIZE2):
                s.append(random.randint(-128, 127))
            self.comp_prototype(s, True)

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
    logging.basicConfig(level=logging.INFO)
    import argparse
    import profile

    unittest.main()
