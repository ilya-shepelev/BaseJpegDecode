# coding:utf-8
# aanIDCT.py 2012.11.5
#
# AANアルゴリズムによる逆DCT
# libjpeg(jpeg-8d)jidctfst.c jidctflt.c からの移植
#
import math
import logging

DCTSIZE = 8
DCTSIZE2 = 64

class aanIDCT: # 整数値演算版
    def __init__(self):
        # 定数の設定
        self.CONST_BITS = 8
        self.PASS1_BITS = 2
        self.SCALE_BITS = 14
        self.LOG2_CONST = int(math.log(self.CONST_BITS, 2)) # 8->3

        # 乗数定数の作成
        self.FIX_1_082392200 = self.SCALEUP(1.082392200, self.CONST_BITS)
        self.FIX_1_414213562 = self.SCALEUP(1.414213562, self.CONST_BITS)
        self.FIX_1_847759065 = self.SCALEUP(1.847759065, self.CONST_BITS)
        self.FIX_2_613125930 = self.SCALEUP(2.613125930, self.CONST_BITS)

        # スケールテーブルの作成
        self.aanscales = [0]*DCTSIZE2
        for v in range(DCTSIZE):
            vs = math.cos(v*math.pi/16) * math.sqrt(2)
            if v == 0:
                vs = 1.0
            for u in range(DCTSIZE):
                us = math.cos(u*math.pi/16) * math.sqrt(2)
                if u == 0:
                    us = 1.0
                val = self.SCALEUP(vs * us / 8.0, self.SCALE_BITS+self.LOG2_CONST)
                self.aanscales[v*DCTSIZE+u] = val

    def SCALEUP(self, x, n):
        return int(x * (1<<(n)))

    def DESCALE(self, x, n):
        return (x / (1<<(n)))

    def DEQUANTIZE(self, coef, quantval):
        return self.DESCALE(coef * quantval, self.SCALE_BITS-self.PASS1_BITS)

    def MULTIPLY(self, a, b):
        return self.DESCALE(a * b, self.CONST_BITS)

    def IDESCALE(self, x):
        return self.DESCALE(x, self.PASS1_BITS+self.LOG2_CONST)

    def conv(self, output, input):
        quant = self.aanscales
        ws = [0]*DCTSIZE2
        for pos in range(DCTSIZE):
            # AC成分が無い場合
            if input[pos+DCTSIZE*1] == 0 and input[pos+DCTSIZE*2] == 0 and \
               input[pos+DCTSIZE*3] == 0 and input[pos+DCTSIZE*4] == 0 and \
               input[pos+DCTSIZE*5] == 0 and input[pos+DCTSIZE*6] == 0 and \
               input[pos+DCTSIZE*7] == 0:
                dcval = self.DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
                for y in range(DCTSIZE):
                    ws[pos+DCTSIZE*y] = dcval
                continue

            # Even part
            tmp0 = self.DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
            tmp1 = self.DEQUANTIZE(input[pos+DCTSIZE*2], quant[pos+DCTSIZE*2])
            tmp2 = self.DEQUANTIZE(input[pos+DCTSIZE*4], quant[pos+DCTSIZE*4])
            tmp3 = self.DEQUANTIZE(input[pos+DCTSIZE*6], quant[pos+DCTSIZE*6])

            tmp10 = tmp0 + tmp2     # phase 3
            tmp11 = tmp0 - tmp2

            tmp13 = tmp1 + tmp3     # phases 5-3
            tmp12 = self.MULTIPLY(tmp1 - tmp3, self.FIX_1_414213562) - tmp13  # 2*c4

            tmp0 = tmp10 + tmp13    # phase 2
            tmp3 = tmp10 - tmp13
            tmp1 = tmp11 + tmp12
            tmp2 = tmp11 - tmp12

            # Odd part
            tmp4 = self.DEQUANTIZE(input[pos+DCTSIZE*1], quant[pos+DCTSIZE*1])
            tmp5 = self.DEQUANTIZE(input[pos+DCTSIZE*3], quant[pos+DCTSIZE*3])
            tmp6 = self.DEQUANTIZE(input[pos+DCTSIZE*5], quant[pos+DCTSIZE*5])
            tmp7 = self.DEQUANTIZE(input[pos+DCTSIZE*7], quant[pos+DCTSIZE*7])

            z13 = tmp6 + tmp5       # phase 6
            z10 = tmp6 - tmp5
            z11 = tmp4 + tmp7
            z12 = tmp4 - tmp7

            tmp7 = z11 + z13        # phase 5
            tmp11 = self.MULTIPLY(z11 - z13, self.FIX_1_414213562)    # 2*c4

            z5 = self.MULTIPLY(z10 + z12, self.FIX_1_847759065)       # 2*c2
            tmp10 = self.MULTIPLY(z12, - self.FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = self.MULTIPLY(z10, - self.FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
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
            # AC成分が無い場合
            if ws[pos+1] == 0 and ws[pos+2] == 0 and ws[pos+3] == 0 and \
               ws[pos+4] == 0 and ws[pos+5] == 0 and ws[pos+6] == 0 and \
               ws[pos+7] == 0:
                dcval = ws[pos+0]
                for x in range(DCTSIZE):
                    output[pos+x] = self.IDESCALE(dcval)
                continue

            # Even part
            tmp10 = ws[pos+0] + ws[pos+4]
            tmp11 = ws[pos+0] - ws[pos+4]

            tmp13 = ws[pos+2] + ws[pos+6]
            tmp12 = self.MULTIPLY(ws[pos+2] - ws[pos+6], self.FIX_1_414213562) - tmp13

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
            tmp11 = self.MULTIPLY(z11 - z13, self.FIX_1_414213562)    # 2*c4

            z5 = self.MULTIPLY(z10 + z12, self.FIX_1_847759065)       # 2*c2
            tmp10 = self.MULTIPLY(z12, - self.FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = self.MULTIPLY(z10, - self.FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
            tmp4 = tmp10 - tmp5

            output[pos+0] = self.IDESCALE(tmp0 + tmp7)
            output[pos+7] = self.IDESCALE(tmp0 - tmp7)
            output[pos+1] = self.IDESCALE(tmp1 + tmp6)
            output[pos+6] = self.IDESCALE(tmp1 - tmp6)
            output[pos+2] = self.IDESCALE(tmp2 + tmp5)
            output[pos+5] = self.IDESCALE(tmp2 - tmp5)
            output[pos+3] = self.IDESCALE(tmp3 + tmp4)
            output[pos+4] = self.IDESCALE(tmp3 - tmp4)


class aanIDCT_f: # 浮動小数点演算版

    def __init__(self):
        self.PASS1_BITS = 2
        self.FIX_1_082392200 = 1.082392200
        self.FIX_1_414213562 = 1.414213562
        self.FIX_1_847759065 = 1.847759065
        self.FIX_2_613125930 = 2.613125930

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

    def DEQUANTIZE(self, coef, quantval):
        return coef * quantval

    def MULTIPLY(self, a, b):
        return a * b

    def IDESCALE(self, x, n):
        return int(x)

    def conv(self, output, input):
        quant = self.aanscales
        ws = [0]*DCTSIZE2
        for pos in range(DCTSIZE):
            if input[pos+DCTSIZE*1] == 0 and input[pos+DCTSIZE*2] == 0 and \
               input[pos+DCTSIZE*3] == 0 and input[pos+DCTSIZE*4] == 0 and \
               input[pos+DCTSIZE*5] == 0 and input[pos+DCTSIZE*6] == 0 and \
               input[pos+DCTSIZE*7] == 0:
                dcval = self.DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
                for y in range(DCTSIZE):
                    ws[pos+DCTSIZE*y] = dcval
                continue

            # Even part
            tmp0 = self.DEQUANTIZE(input[pos+DCTSIZE*0], quant[pos+DCTSIZE*0])
            tmp1 = self.DEQUANTIZE(input[pos+DCTSIZE*2], quant[pos+DCTSIZE*2])
            tmp2 = self.DEQUANTIZE(input[pos+DCTSIZE*4], quant[pos+DCTSIZE*4])
            tmp3 = self.DEQUANTIZE(input[pos+DCTSIZE*6], quant[pos+DCTSIZE*6])

            tmp10 = tmp0 + tmp2     # phase 3
            tmp11 = tmp0 - tmp2

            tmp13 = tmp1 + tmp3     # phases 5-3
            tmp12 = self.MULTIPLY(tmp1 - tmp3, self.FIX_1_414213562) - tmp13  # 2*c4

            tmp0 = tmp10 + tmp13    # phase 2
            tmp3 = tmp10 - tmp13
            tmp1 = tmp11 + tmp12
            tmp2 = tmp11 - tmp12

            # Odd part
            tmp4 = self.DEQUANTIZE(input[pos+DCTSIZE*1], quant[pos+DCTSIZE*1])
            tmp5 = self.DEQUANTIZE(input[pos+DCTSIZE*3], quant[pos+DCTSIZE*3])
            tmp6 = self.DEQUANTIZE(input[pos+DCTSIZE*5], quant[pos+DCTSIZE*5])
            tmp7 = self.DEQUANTIZE(input[pos+DCTSIZE*7], quant[pos+DCTSIZE*7])

            z13 = tmp6 + tmp5       # phase 6
            z10 = tmp6 - tmp5
            z11 = tmp4 + tmp7
            z12 = tmp4 - tmp7

            tmp7 = z11 + z13        # phase 5
            tmp11 = self.MULTIPLY(z11 - z13, self.FIX_1_414213562)    # 2*c4

            z5 = self.MULTIPLY(z10 + z12, self.FIX_1_847759065)       # 2*c2
            tmp10 = self.MULTIPLY(z12, - self.FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = self.MULTIPLY(z10, - self.FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
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
                    output[pos+x] = self.IDESCALE(dcval, self.PASS1_BITS+3)
                continue

            # Even part
            tmp10 = ws[pos+0] + ws[pos+4]
            tmp11 = ws[pos+0] - ws[pos+4]

            tmp13 = ws[pos+2] + ws[pos+6]
            tmp12 = self.MULTIPLY(ws[pos+2] - ws[pos+6], self.FIX_1_414213562) - tmp13

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
            tmp11 = self.MULTIPLY(z11 - z13, self.FIX_1_414213562)    # 2*c4

            z5 = self.MULTIPLY(z10 + z12, self.FIX_1_847759065)       # 2*c2
            tmp10 = self.MULTIPLY(z12, - self.FIX_1_082392200) + z5   # 2*(c2-c6)
            tmp12 = self.MULTIPLY(z10, - self.FIX_2_613125930) + z5   # -2*(c2+c6)

            tmp6 = tmp12 - tmp7     # phase 2
            tmp5 = tmp11 - tmp6
            tmp4 = tmp10 - tmp5

            output[pos+0] = self.IDESCALE(tmp0 + tmp7, self.PASS1_BITS+3)
            output[pos+7] = self.IDESCALE(tmp0 - tmp7, self.PASS1_BITS+3)
            output[pos+1] = self.IDESCALE(tmp1 + tmp6, self.PASS1_BITS+3)
            output[pos+6] = self.IDESCALE(tmp1 - tmp6, self.PASS1_BITS+3)
            output[pos+2] = self.IDESCALE(tmp2 + tmp5, self.PASS1_BITS+3)
            output[pos+5] = self.IDESCALE(tmp2 - tmp5, self.PASS1_BITS+3)
            output[pos+3] = self.IDESCALE(tmp3 + tmp4, self.PASS1_BITS+3)
            output[pos+4] = self.IDESCALE(tmp3 - tmp4, self.PASS1_BITS+3)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse
    import profile

    class TableAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            idct = aanIDCT()
            d = [
                ("DCTSIZE", DCTSIZE),
                ("DCTSIZE2", DCTSIZE2),
                ("CONST_BITS", idct.CONST_BITS),
                ("PASS1_BITS", idct.PASS1_BITS),
                ("SCALE_BITS", idct.SCALE_BITS),
                ("LOG2_CONST", idct.LOG2_CONST),
                ("FIX_1_082392200", idct.FIX_1_082392200),
                ("FIX_1_414213562", idct.FIX_1_414213562),
                ("FIX_1_847759065", idct.FIX_1_847759065),
                ("FIX_2_613125930", idct.FIX_2_613125930)
            ]
            for v in d:
                print "#define %s %d" % v

            print "const uint16_t aanscales[] = {"
            for i,v in enumerate(idct.aanscales):
                print "%5d," % v,
                if i%8 == 7:
                    print
            print "};"

    class CppAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print values[0]

    parser = argparse.ArgumentParser()
    parser.add_argument('--table', nargs='*', action=TableAction)
    parser.add_argument('--cpp', nargs=1, action=CppAction)
    args = parser.parse_args()
