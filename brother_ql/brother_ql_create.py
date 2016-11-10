#!/usr/bin/env python

from __future__ import division

import sys, argparse, logging

import numpy as np
from PIL import Image

from brother_ql.raster import BrotherQLRaster
from brother_ql.devicedependent import models, label_type_specs, ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL
from brother_ql import BrotherQLError, BrotherQLUnsupportedCmd, BrotherQLUnknownModel

try:
    stdout = sys.stdout.buffer
except:
    stdout = sys.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='The image file to create a label from.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('wb'), default=stdout, help='The file to write the instructions to. Defaults to stdout.')
    parser.add_argument('--model', '-m', default='QL-500', help='The printer model to use. Check available ones with `brother_ql_info --list-models`.')
    parser.add_argument('--label-size', '-s', default='62', help='The label size (and kind) to use. Check available ones with `brother_ql_info --list-label-sizes`.')
    parser.add_argument('--threshold', '-t', type=float, default=70.0, help='The threshold value (in percent) to discriminate between black and white pixels.')
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING, help='Set to DEBUG for verbose debugging output to stderr.')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    args.model = args.model.upper()

    try:
        qlr = BrotherQLRaster(args.model)
    except BrotherQLUnknownModel:
        sys.exit("Unknown model. Use the command   brother_ql_info --list-models   to show available models.")

    try:
        label_type_specs[args.label_size]
    except ValueError:
        sys.exit("Unknown label_size. Check available sizes with the command   brother_ql_info --list-label-sizes")

    qlr.exception_on_warning = True

    create_label(qlr, args.image, args.label_size, threshold=args.threshold)

    args.outfile.write(qlr.data)

def create_label(qlr, image, label_size, threshold=70, **kwargs):

    label_specs = label_type_specs[label_size]

    if label_specs['kind'] == ENDLESS_LABEL:
        device_pixel_width = qlr.get_pixel_width()
        im = Image.open(image)
        hsize = int(im.size[1] / im.size[0] * device_pixel_width)
        im = im.resize((device_pixel_width, hsize), Image.ANTIALIAS)
        im = im.convert("L")
        arr = np.asarray(im, dtype=np.uint8)
        arr.flags.writeable = True
        white_idx = arr[:,:] <  threshold
        black_idx = arr[:,:] >= threshold
        arr[white_idx] = 1
        arr[black_idx] = 0
    elif label_specs['kind'] == DIE_CUT_LABEL:
        dots_printable = label_specs['dots_printable']
        im = Image.open(image)
        im = im.convert("L")
        if im.size[0] == dots_printable[1] and im.size[1] == dots_printable[0]:
            im = im.rotate(90, expand=True)
        if im.size[0] != dots_printable[0] or im.size[1] != dots_printable[1]:
            sys.exit("Check your image dimensions. Expecting: " + str(dots_printable))
        new_im = Image.new(im.mode, (720, dots_printable[1]), 255)
        new_im.paste(im, (720-im.size[0], 0))
        im = new_im
        arr = np.asarray(im, dtype=np.uint8)
        arr.flags.writeable = True
        white_idx = arr[:,:] <  threshold
        black_idx = arr[:,:] >= threshold
        arr[white_idx] = 1
        arr[black_idx] = 0
    else:
        raise NotImplementedError("Label kind %s not implemented yet." % label_specs['kind'])

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
    tape_size = label_specs['tape_size']
    if label_specs['kind'] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
        qlr.mtype = 0x0B
        qlr.mwidth = tape_size[0]
        qlr.mlength = tape_size[1]
    else:
        qlr.mtype = 0x0A
        qlr.mwidth = tape_size[0]
        qlr.mlength = 0
    qlr.pquality = 1
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
    if label_specs['kind'] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
        qlr.add_margins(dots=0)
    else:
        qlr.add_margins()
    try:
        qlr.add_compression(True)
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_raster_data(arr)
    qlr.add_print()

if __name__ == "__main__":
    main()
