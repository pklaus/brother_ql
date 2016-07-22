#!/usr/bin/env python

from __future__ import division

import sys, argparse, logging

import numpy as np
from PIL import Image

from brother_ql.raster import BrotherQLRaster
from brother_ql.devicedependent import models
from brother_ql import BrotherQLError, BrotherQLUnsupportedCmd, BrotherQLUnknownModel

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
    parser.add_argument('--list-models', action='store_true', \
      help='List available models and quit (the image argument is still required but ignored)')
    parser.add_argument('--threshold', type=int, default=170)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING)
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    args.model = args.model.upper()

    if args.list_models:
        print('Supported models:')
        print('\n'.join(models))
        sys.exit(0)

    try:
        qlr = BrotherQLRaster(args.model)
    except BrotherQLUnknownModel:
        sys.exit("Unknown model. Use option --list-models to show available models.")
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
    qlr.add_status_information()
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

    args.outfile.write(qlr.data)

if __name__ == "__main__":
    main()
