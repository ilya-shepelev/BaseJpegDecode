# coding:utf-8
# test_SimpleJpegDecode.py 2012.11.3
import SimpleJpegDecode
import bmp24
import unittest

class TestSimpleJpegDecode(unittest.TestCase):
    def setUp(self):
        self.infiles = [
            "../lifecam/cam0001.jpg",
            "../c270/cam0001.jpg",
            "book.jpg"
        ]
        self.bmp = bmp24.bmp24()

    def test_decode_None(self):
        decode = SimpleJpegDecode.SimpleJpegDecode()
        for i, filename in enumerate(self.infiles):
            with open(filename, "rb") as f:
                data = f.read()
            print("%s %d" % (filename, len(data)))
            decode.clear()
            for c in data:
                decode.input(ord(c))

    def callbackYUV(self, x, y, yuv):
        rgb = SimpleJpegDecode.convYUVtoRGB(yuv[0], yuv[1], yuv[2])
        self.bmp.point(x, y, rgb)

    def test_decode_YUV(self):
        decode = SimpleJpegDecode.SimpleJpegDecode(self.callbackYUV,SimpleJpegDecode.YUV)
        for i, filename in enumerate(self.infiles):
            with open(filename, "rb") as f:
                data = f.read()
            print("%s %d" % (filename, len(data)))
            self.bmp.clear()
            decode.clear()
            for c in data:
                decode.input(ord(c))

    def callbackRGB(self, x, y, rgb):
        self.bmp.point(x, y, rgb)

    def test_decode_RGB24(self):
        decode = SimpleJpegDecode.SimpleJpegDecode(self.callbackRGB)
        for i, filename in enumerate(self.infiles):
            with open(filename, "rb") as f:
                data = f.read()
            print("input: %s %d" % (filename, len(data)))
            self.bmp.clear()
            decode.clear()
            for c in data:
                decode.input(ord(c))

            image_data = self.bmp.output_string()
            output_filename = "output%d.bmp" % i
            print "output: %s" % output_filename
            with open(output_filename, "wb") as f:
                f.write(image_data)
