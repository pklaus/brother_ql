#!/usr/bin/env python

from __future__ import division

import sys, argparse, logging

import numpy as np
from PIL import Image

from brother_ql.raster import BrotherQLRaster
from brother_ql import BrotherQLError, BrotherQLUnsupportedCmd

try:
    stdout = sys.stdout.buffer
except:
    stdout = sys.stdout

def hex_format(data):
    return ' '.join('{:02X}'.format(byte) for byte in data)

def multiline_hex(data, bpl):
    """ data: bytes, bpl: int (bytes to be displayed per line) """
    data = hex_format(data).split()
    data = [' '.join(data[i:i+bpl]) for i in range(0, len(data), bpl)]
    return '\n'.join(data) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('wb'), default=stdout)
    parser.add_argument('--model', default='QL-500')
    parser.add_argument('--threshold', type=int, default=170)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING)
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    qlr = BrotherQLRaster(args.model)
    qlr.exception_on_warning = True
    device_pixel_width = qlr.get_pixel_width()

    im = Image.open(args.image)
    hsize = int(im.size[1] / im.size[0] * device_pixel_width)
    im = im.resize((device_pixel_width, hsize), Image.ANTIALIAS)
    im = im.convert("L")
    arr = np.asarray(im, dtype=np.uint8)
    arr.flags.writeable = True
    white_idx = arr[:,:] <  args.threshold
    black_idx = arr[:,:] >= args.threshold
    arr[white_idx] = 1
    arr[black_idx] = 0


    try:
        qlr.add_switch_mode()
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_invalidate()
    qlr.add_initialize()
    try:
        qlr.add_switch_mode()
    except BrotherQLUnsupportedCmd:
        pass
    qlr.mtype = 0x0A
    qlr.mwidth = 62
    qlr.mlength = 0
    qlr.add_media_and_quality(im.size[1])
    try:
        qlr.add_autocut(True)
        qlr.add_cut_every(1)
    except BrotherQLUnsupportedCmd:
        pass
    try:
        qlr.dpi_600 = False
        qlr.cut_at_end = True
        qlr.add_expanded_mode()
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_margins()
    try:
        qlr.add_compression(True)
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_raster_data(arr)
    qlr.add_print()

    if args.loglevel == logging.DEBUG:
        sys.stderr.write(multiline_hex(qlr.data, 16))

    args.outfile.write(qlr.data)

if __name__ == "__main__":
    main()
