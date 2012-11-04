# coding:utf-8
# SimpleJpegDecode.py 2012.11.4
import copy
import logging
import BaseJpegDecode
import inverseDCT

def adjust(value):
    value += 128
    if value < 0:
        return 0
    elif value > 255:
        return 255
    return int(value)

class my_idct(inverseDCT.inverseDCT_aan_f):
    def __init__(self, callback=None):
        super(my_idct, self).__init__()
        self._callback = callback

    def outputBLOCK(self, mcu, block, values):
        if self._callback:
            self._callback(mcu, block, values)

# 出力形式
YUV   = 0
RGB24 = 1

def convYUVtoRGB(y, u, v):
    Q=32
    r = int(y*Q + v * (1.4020*Q))/Q                  + 128
    g = int(y*Q - u * (0.3441*Q) - v * (0.7139*Q))/Q + 128
    b = int(y*Q + u * (1.7718*Q) - v * (0.0012*Q))/Q + 128
    if r > 255:
        r = 255
    elif r < 0:
        r = 0
    if g > 255:
        g = 255
    elif g < 0:
        g = 0
    if b > 255:
        b = 255
    elif b < 0:
       b = 0
    return [r, g, b]

def convYUVtoRGB_f(y, u, v):
    r = int(y + v * 1.4020)              + 128
    g = int(y - u * 0.3441 - v * 0.7139) + 128
    b = int(y + u * 1.7718 - v * 0.0012) + 128
    if r > 255:
        r = 255
    elif r < 0:
        r = 0
    if g > 255:
        g = 255
    elif g < 0:
        g = 0
    if b > 255:
        b = 255
    elif b < 0:
       b = 0
    return [r, g, b]

class SimpleJpegDecode(BaseJpegDecode.BaseJpegDecode):
    def __init__(self, callback=None, output_mode=RGB24):
        super(SimpleJpegDecode, self).__init__()
        self._idct = my_idct(self.outputBLOCK)
        self._callback = callback # callback(x, y, data)
        self._output_mode = output_mode


    def _format_YUV(self, mcu, block, values):
        if block == 0:
            self.block_data = {}
        if block < self._yblock+1: # Y0,Y1,Cb or Y0,Y1,Y2,Y3,Cb
            self.block_data[block] = copy.deepcopy(values)
            return
        mcu_x = mcu % (self.width/16)
        mcu_y = mcu / (self.width/16)
        if self._yblock == 2:
            for y in range(8):
                for x in range(16):
                    yuv_y = self.block_data[x/8][y*8+x%8]
                    yuv_u = self.block_data[2][y*8+x/2]
                    yuv_v = values[y*8+x/2]
                    yuv = [yuv_y+128, yuv_u+128, yuv_v+128]
                    if self._callback:
                        self._callback(mcu_x * 16 + x, mcu_y * 8 + y, yuv)
        elif self._yblock == 4:
            for y in range(16):
                for x in range(16):
                    yuv_y = self.block_data[(y/8)*2+x/8][(y%8)*8+x%8]
                    yuv_u = self.block_data[4][(y/2)*8+x/2]
                    yuv_v = values[(y/2)*8+x/2]
                    yuv = [yuv_y+128, yuv_u+128, yuv_v+128]
                    if self._callback:
                        self._callback(mcu_x * 16 + x, mcu_y * 16 + y, yuv)
        else:
            raise ValueError('yblock error')

    def _format_RGB24(self, mcu, block, values):
        if block == 0:
            self.block_data = {}
        if block < self._yblock+1: # Y0,Y1,Cb or Y0,Y1,Y2,Y3,Cb
            self.block_data[block] = copy.deepcopy(values)
            return
        mcu_x = mcu % (self.width/16)
        mcu_y = mcu / (self.width/16)
        if self._yblock == 2:
            for y in range(8):
                for x in range(16):
                    yuv_y = self.block_data[x/8][y*8+x%8]
                    yuv_u = self.block_data[2][y*8+x/2]
                    yuv_v = values[y*8+x/2]
                    rgb = convYUVtoRGB(yuv_y, yuv_u, yuv_v)
                    if self._callback:
                        self._callback(mcu_x * 16 + x, mcu_y * 8 + y, rgb)
        elif self._yblock == 4:
            for y in range(16):
                for x in range(16):
                    yuv_y = self.block_data[(y/8)*2+x/8][(y%8)*8+x%8]
                    yuv_u = self.block_data[4][(y/2)*8+x/2]
                    yuv_v = values[(y/2)*8+x/2]
                    rgb = convYUVtoRGB(yuv_y, yuv_u, yuv_v)
                    if self._callback:
                        self._callback(mcu_x * 16 + x, mcu_y * 16 + y, rgb)
        else:
            raise ValueError('yblock error')

    def outputBLOCK(self, mcu, block, values):
        if self._output_mode == YUV:
            self._format_YUV(mcu, block, values)
        elif self._output_mode == RGB24:
            self._format_RGB24(mcu, block, values)
        else:
            raise ValueError('output_mode error')

    def _output(self, mcu, block, scan, value):
        if block < self._yblock:
            sc = 0
        else:
            sc = 1
        self._idct.inputBLOCK(mcu, block, scan, value * self.qt[sc][scan]) # 逆量子化,逆DCT

    def outputDC(self, mcu, block, value):
        self._output(mcu, block, 0, value)
        if mcu == 0 and block == 0:
            self._info_s = ""
        if block == 0:
            self._info_s += "%02X " % adjust(value * self.qt[0][0] / 8)
            if (mcu % (self.width/16)) == (self.width/16)-1:
                logging.info(self._info_s)
                self._info_s = ""

    def outputAC(self, mcu, block, scan, value):
        self._output(mcu, block, scan, value)

    def outputMARK(self, c):
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    import argparse

    def jpg2bmp(filename):
        with open(filename, "rb") as f:
            data = f.read()
        print("%s %d" % (filename, len(data)))
        decode = SimpleJpegDecode()
        decode.clear()
        for c in data:
            decode.input(ord(c))

    class ProfileAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            import profile
            s = 'jpg2bmp("%s")' % values[0]
            profile.run(s)

    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', nargs=1, action=ProfileAction)
    parser.add_argument('infiles', nargs='*', help=u"入力JPEGファイル")
    parser.add_argument('--output', nargs=1, help=u"出力BMPファイル")
    args = parser.parse_args()

    import bmp24
    bmp = bmp24.bmp24()

    def callbackRGB(x, y, rgb):
        bmp.point(x, y, rgb)

    decode = SimpleJpegDecode(callbackRGB, RGB24)

    for i, filename in enumerate(args.infiles):
        with open(filename, "rb") as f:
            data = f.read()
        print("input: %s %d" % (filename, len(data)))
        decode.clear()
        for c in data:
            decode.input(ord(c))

        bmp.width = decode.width
        bmp.height = decode.height
        image_data = bmp.output_string()
        output_filename = "output%d.bmp" % i
        if args.output:
            output_filename = args.output[0]
        with open(output_filename, "wb") as f:
            f.write(image_data)
        print "output: %s" % output_filename
