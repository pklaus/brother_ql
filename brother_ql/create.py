#!/usr/bin/env python

import sys, argparse, logging

import numpy as np
from PIL import Image

from brother_ql.raster import BrotherQLRaster

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
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('wb'), default=sys.stdout.buffer)
    parser.add_argument('--model', default='QL-500')
    parser.add_argument('--threshold', type=int, default=170)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING)
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    im = Image.open(args.image)
    im = im.convert("L")
    arr = np.asarray(im, dtype=np.uint8)
    arr.flags.writeable = True
    white_idx = arr[:,:] <  args.threshold
    black_idx = arr[:,:] >= args.threshold
    arr[white_idx] = 1
    arr[black_idx] = 0

    qlr = BrotherQLRaster(args.model)
    qlr.set_mode()
    qlr.set_clear_command_buffer()
    qlr.set_initialize()
    qlr.set_mode()
    qlr.mtype = 0x0A
    qlr.mwidth = 62
    qlr.mlength = 0
    qlr.set_media_and_quality(im.size[1])
    qlr.set_autocut(True)
    qlr.set_cut_every(1)
    qlr.dpi_600 = False
    qlr.cut_at_end = True
    qlr.set_expanded_mode()
    qlr.set_margins()
    qlr.set_compression(True)
    qlr.set_raster_data(arr)
    qlr.print()

    if args.loglevel == logging.DEBUG:
        sys.stderr.write(multiline_hex(qlr.data, 16))

    args.outfile.write(qlr.data)

if __name__ == "__main__":
    main()
