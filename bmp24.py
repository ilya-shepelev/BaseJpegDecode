# coding:utf-8
# bmp24.py 2012.10.30
import logging

def CHECK_RANGE(data):
    if data < 0:
        raise ValueError('range 0 error')
    if data > 255:
        raise ValueError('range 255 error')

def LE32write(buf, i, value):
    buf[i] = value & 0xff
    buf[i+1] = (value>>8) & 0xff
    buf[i+2] = (value>>16) & 0xff
    buf[i+3] = (value>>24) & 0xff

class bmp24():
    def __init__(self, width = 160, height = 120):
        self.clear()
        self.width = width
        self.height = height
        self.header = [
0x42,0x4d,0x36,0xe1,0x00,0x00,0x00,0x00,0x00,0x00,0x36,0x00,0x00,0x00,0x28,0x00,
0x00,0x00,0xa0,0x00,0x00,0x00,0x78,0x00,0x00,0x00,0x01,0x00,0x18,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00]

    def clear(self):
        self._bitmap = {}

    def point(self, x, y, rgb=(0,0,0)):
        self._bitmap[(x, y)] = rgb
        CHECK_RANGE(rgb[0])
        CHECK_RANGE(rgb[1])
        CHECK_RANGE(rgb[2])

    def output_string(self):
        width3 = self.width * 3
        null_count = 0
        if (width3 % 4) != 0:
            null_count = 4 - (width3 % 4)
            width3 += null_count
        file_size = len(self.header) + width3 * self.height
        self.header[0:2] = [0x42, 0x4d]
        LE32write(self.header, 2, file_size)
        LE32write(self.header, 18, self.width)
        LE32write(self.header, 22, self.height)
        r = ""
        for c in self.header:
            r += chr(c)
        for y in range(self.height-1, -1, -1):
            for x in range(self.width):
                if (x, y) in self._bitmap:
                    rgb = self._bitmap[(x, y)]
                else:
                    rgb = (255, 255, 255)
                r += chr(rgb[2]) + chr(rgb[1]) + chr(rgb[0])
            for i in range(null_count):
                r += chr(0x00)
        logging.info("BMP length: %d" % len(r))
        return r

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)

    image = bmp24(320,240)
    for y in range(image.height):
        image.point(y, y, (255,0,0))
        image.point(y+2, y, (0,255,0))
        image.point(y+4, y, (0,0,255))
        image.point(y+6, y)
    image_data = image.output_string()
    with open("output.bmp", "wb") as f:
        f.write(image_data)
