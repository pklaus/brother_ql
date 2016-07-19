#!/usr/bin/env python

import struct
import io
import logging
import sys

from PIL import Image
import numpy as np
from matplotlib import pyplot as plt

logger = logging.getLogger(__name__)

cmds = {
    # signature              name    following bytes   description
    b'\x00':                 ("preamble",       -1, "Preamble, 200-300x 0x00 to clear comamnd buffer"),
    b'\x4D':                 ("compression",     1, ""),
    b'\x67':                 ("raster",         -1, ""),
    b'\x0C':                 ("print",           0, "print intermediate page"),
    b'\x1A':                 ("print",           0, "print final page"),
    b'\x1b\x40':             ("init",            0, "initialization"),
    b'\x1b\x69\x61':         ("mode setting",    1, ""),
    b'\x1b\x69\x7A':         ("media/quality",  10, "print-media and print-quality"),
    b'\x1b\x69\x4D':         ("various",         1, "Auto cut flag in bit 7"),
    b'\x1b\x69\x41':         ("cut-every",       1, "cut every n-th page"),
    b'\x1b\x69\x4B':         ("expanded",        1, ""),
    b'\x1b\x69\x64':         ("margins",         2, ""),
    b'\x1b\x69\x55\x77\x01': ('amedia',        127, "Additional media information command"),
    b'\x1b\x69\x55\x4A':     ('jobid',          14, "Job ID setting command"),
}

dot_widths = {
  62: 90*8,
}

def hex_format(data):
    try: # Py3
        return ' '.join('{:02X}'.format(byte) for byte in data)
    except ValueError: # Py2
        return ' '.join('{:02X}'.format(ord(byte)) for byte in data)

def chunker(data, raise_exception=False):
    """
    Breaks data stream (bytes) into a list of bytes containing single instructions each.

    Logs warnings for unknown commands.
    If raise_exception is set to True it raise exceptions instead.

    returns: list of bytes
    """
    instructions = []
    while True:
        if len(data) == 0: break
        cmd_found = False
        for command in cmds.keys():
            if data.startswith(command):
                cmd = cmds[command]
                num_bytes = len(command)
                if cmd[1] > 0: num_bytes += cmd[1]
                if cmd[0] == 'raster':
                    num_bytes += data[2] + 2
                #payload = data[len(command):num_bytes]
                instructions.append(data[:num_bytes])
                data = data[num_bytes:]
                cmd_found = True
        if cmd_found:
            continue
        else:
            msg = 'unknown instruction starting with {}...)'.format(hex_format(data[0:4]))
            if raise_exception:
                raise ValueError(msg)
            else:
                logger.warning(msg)
                data = data[1:]
    return instructions

class BrotherQLReader(object):

    def __init__(self, brother_file):
        if type(brother_file) in (str,):
            brother_file = io.open(brother_file, 'rb')
        self.brother_file = brother_file
        self.mwidth, self.mheight = None, None
        self.raster_no = None
        self.rows = []
        self.compression = False
        self.page = 1

    def analyse(self):
        instructions = self.brother_file.read()
        for instruction in chunker(instructions):
            for command in cmds.keys():
                if instruction.startswith(command):
                    cmd = cmds[command]
                    if cmd[0] == 'init':
                        self.mwidth, self.mheight = None, None
                        self.raster_no = None
                        self.rows = []
                    payload = instruction[len(command):]
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
                            row.append(list(rpl))
                        self.rows.append(row)
                    if cmd[0] == 'media/quality':
                        self.raster_no = struct.unpack('<L', payload[4:8])[0]
                        self.mwidth = instruction[len(command) + 2]
                        self.mlength = instruction[len(command) + 3]*256
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
                        img_name = 'page{:04d}.png'.format(self.page)
                        im.save(img_name)
                        print('Page saved as {}'.format(img_name))
                        self.page += 1
