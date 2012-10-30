# coding:utf-8
# SimpleJpegDecode.py 2012.10.30
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

class my_idct(inverseDCT.inverseDCT):
    def __init__(self, callback=None):
        super(my_idct, self).__init__()
        self._callback = callback

    def outputBLOCK(self, mcu, block, values):
        if self._callback:
            self._callback(mcu, block, values)

class SimpleJpegDecode(BaseJpegDecode.BaseJpegDecode):
    def __init__(self, callbackYUV=None):
        super(SimpleJpegDecode, self).__init__()
        self._idct = my_idct(self.outputBLOCK)
        self._callbackYUV = callbackYUV # callback(x, y, yuv)

    def outputBLOCK(self, mcu, block, values):
        if block == 0:
            self.block_data = {}
        self.block_data[block] = copy.deepcopy(values)
        if block == self._yblock+1: # last 3 or 5
            mcu_x = mcu % (self.width/16)
            mcu_y = mcu / (self.width/16)
            if self._yblock == 2:
                for y in range(8):
                    for x in range(16):
                        value = self.block_data[x/8][y*8+x%8]
                        u = self.block_data[2][y*8+x/2]
                        v = self.block_data[3][y*8+x/2]
                        yuv = (value, u, v)
                        if self._callbackYUV:
                            self._callbackYUV(mcu_x * 16 + x, mcu_y * 8 + y, yuv)
            elif self._yblock == 4:
                for y in range(16):
                    for x in range(16):
                        block = (y/8)*2+x/8
                        value = self.block_data[block][(y%8)*8+x%8]
                        u = self.block_data[4][(y/2)*8+x/2]
                        v = self.block_data[5][(y/2)*8+x/2]
                        yuv = (value, u, v)
                        if self._callbackYUV:
                            self._callbackYUV(mcu_x * 16 + x, mcu_y * 16 + y, yuv)
            else:
                raise ValueError('yblock error')

    def _output(self, mcu, block, scan, value):
        if block < self._yblock:
            sc = 0
        else:
            sc = 1
        self._idct.inputBLOCK(mcu, block, scan, value * self.qt[sc][scan]) # 逆量子化,逆DCT

    def outputDC(self, mcu, block, value):
        self._output(mcu, block, 0, value)
        if block == 0:
            print("%02X" % adjust(value * self.qt[0][0] / 8)),
            if (mcu % (self.width/16)) == (self.width/16)-1:
                print

    def outputAC(self, mcu, block, scan, value):
        self._output(mcu, block, scan, value)

    def outputMARK(self, c):
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    import argparse
    import bmp24

    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='*')
    args = parser.parse_args()

    bmp = bmp24.bmp24()
    
    def callbackYUV(x, y, yuv):
        r = int(yuv[0] + (yuv[2]-128) * 1.4020)
        if r < 0:
            r = 0
        elif r > 255:
            r = 255
        g = int(yuv[0] - (yuv[1]-128) * 0.3441 - (yuv[2]-128) * 0.7139)
        if g < 0:
            g = 0
        elif g > 255:
            g = 255
        b = int(yuv[0] + (yuv[1]-128) * 1.7718 - (yuv[2]-128) * 0.0012)
        if b < 0:
            b = 0
        elif b > 255:
            b = 255
        rgb = (r, g, b)
        #rgb = (yuv[1], yuv[1], yuv[1])
        #rgb = (yuv[2], yuv[2], yuv[2])
        bmp.point(x, y, rgb)

    decode = SimpleJpegDecode(callbackYUV)

    for i, filename in enumerate(args.infiles):
        with open(filename, "rb") as f:
            data = f.read()
        print("%s %d" % (filename, len(data)))
        decode.clear()
        for c in data:
            decode.input(ord(c))

        bmp.width = decode.width
        bmp.height = decode.height
        image_data = bmp.output_string()
        output_filename = "output%d.bmp" % i
        with open(output_filename, "wb") as f:
            f.write(image_data)
        print output_filename
