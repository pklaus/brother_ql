#!/usr/bin/env python

import struct
import io
import logging

from PIL import Image
import numpy as np
from matplotlib import pyplot as plt

logger = logging.getLogger(__name__)

cmds = {
    # signature      name    following bytes   description
    b'\x00':          ("preamble",       0, "Preamble, 200-300x 0x00 to clear comamnd buffer"),
    b'\x4D':          ("compression",    1, ""),
    b'\x67':          ("raster",        -1, ""),
    b'\x0C':          ("print",          0, "print intermediate page"),
    b'\x1A':          ("print",          0, "print final page"),
    b'\x1b\x40':      ("init",           0, "initialization"),
    b'\x1b\x69\x61':  ("mode setting",   1, ""),
    b'\x1b\x69\x7A':  ("media/quality", 10, "print-media and print-quality"),
    b'\x1b\x69\x4D':  ("set mode",       1, ""),
    b'\x1b\x69\x41':  ("cuts-settings",  1, "cut every n setting"),
    b'\x1b\x69\x4B':  ("cut type",       1, ""),
    b'\x1b\x69\x64':  ("margins",        2, ""),
    b'\x1b\x69\x55\x77\x01': ('amedia',127, "Additional media information command"),
    b'\x1b\x69\x55\x4A': ('jobid',      14, "Job ID setting command"),
}

dot_widths = {
  62: 90*8,
}

def hex_format(data):
    return ' '.join('{:02X}'.format(byte) for byte in data)

class BrotherReader(object):

    def __init__(self, brother_file):
        if type(brother_file) in (str,):
            brother_file = io.open(brother_file, 'rb')
        self.brother_file = brother_file
        self.mwidth, self.mheight = None, None
        self.raster_no = None
        self.rows = []
        self.compression = False
        self.page = 1

    def analyze(self):
        rem_script = self.brother_file.read()
        while True:
            if len(rem_script) == 0: break
            cmd_found = False
            for command in cmds.keys():
                if rem_script.startswith(command):
                    cmd = cmds[command]
                    num_bytes = len(command)
                    if cmd[1] > 0: num_bytes += cmd[1]
                    if cmd[0] == 'init':
                        self.mwidth, self.mheight = None, None
                        self.raster_no = None
                        self.rows = []
                    if cmd[0] == 'raster':
                        num_bytes += rem_script[2] + 2
                    payload = rem_script[len(command):num_bytes]
                    # now num_bytes and payload are accessable
                    logger.info(" {} ({}) --> found! (payload: {})".format(cmd[0], hex_format(command), hex_format(payload)))
                    if cmd[0] == 'compression':
                        self.compression = payload[0] == 0x02
                    if cmd[0] == 'raster':
                        rpl = payload[2:] # raster payload
                        index = 0
                        row = []
                        if self.compression:
                            while True:
                                num = rpl[index]
                                if num & 0x80:
                                    num = num - 0x100
                                if num < 0:
                                    num = -num + 1
                                    for i in range(num): row.append(rpl[index+1])
                                    index += 2
                                else:
                                    num = num + 1
                                    for i in range(num): row.append(rpl[index+1+i])
                                    index += 1 + num
                                if index >= len(rpl): break
                        else:
                            raise NotImplementedError()
                        self.rows.append(row)
                    if cmd[0] == 'media/quality':
                        self.raster_no = struct.unpack('<L', payload[4:8])[0]
                        self.mwidth = rem_script[len(command) + 2]
                        self.mlength = rem_script[len(command) + 3]*256
                        fmt = " media width: {}mm, media length: {}mm, raster no: {}dots"
                        logger.info(fmt.format(self.mwidth, self.mlength, self.raster_no))
                    if cmd[0] == 'print':
                        self.rows = [np.unpackbits(np.array(row, dtype=np.uint8)) for row in self.rows]
                        array = np.array(self.rows, dtype=np.uint8)
                        array = np.fliplr(array)
                        im = Image.fromarray(array)
                        im = im.point(lambda x: 0 if x == 1 else 255, '1') # -> Monocolor and invert
                        #plt.imshow(im)
                        #plt.show()
                        im.save('image{:04d}.png'.format(self.page))
                        self.page += 1

                    rem_script = rem_script[num_bytes:]
                    cmd_found = True
            if cmd_found:
                continue
            else:
                logger.error('cmd not found: {}...'.format(rem_script[0:4]))
                rem_script = rem_script[1:]

if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('file', help='The file to analyze')
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING, help='The loglevel to apply')
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=args.loglevel)

    br = BrotherReader(args.file)
    br.analyze()
