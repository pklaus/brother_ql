#!/usr/bin/env python

from __future__ import division

import sys, argparse, logging

from PIL import Image

from brother_ql.raster import BrotherQLRaster
from brother_ql.devicedependent import models, label_type_specs, ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL
from brother_ql import BrotherQLError, BrotherQLUnsupportedCmd, BrotherQLUnknownModel

try:
    stdout = sys.stdout.buffer
except:
    stdout = sys.stdout

try:
    unicode
except:
    unicode = str

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('image', help='The image file to create a label from.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('wb'), default=stdout, help='The file to write the instructions to. Defaults to stdout.')
    parser.add_argument('--model', '-m', default='QL-500', help='The printer model to use. Check available ones with `brother_ql_info list-models`.')
    parser.add_argument('--label-size', '-s', default='62', help='The label size (and kind) to use. Check available ones with `brother_ql_info list-label-sizes`.')
    parser.add_argument('--rotate', '-r', choices=('0', '90', '180', '270'), default='auto', help='Rotate the image (counterclock-wise) by this amount of degrees.')
    parser.add_argument('--threshold', '-t', type=float, default=70.0, help='The threshold value (in percent) to discriminate between black and white pixels.')
    parser.add_argument('--no-cut', dest='cut', action='store_false', help="Don't cut the tape after printing the label.")
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING, help='Set to DEBUG for verbose debugging output to stderr.')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

    args.model = args.model.upper()

    try:
        qlr = BrotherQLRaster(args.model)
    except BrotherQLUnknownModel:
        sys.exit("Unknown model. Use the command   brother_ql_info list-models   to show available models.")

    try:
        label_type_specs[args.label_size]
    except ValueError:
        sys.exit("Unknown label_size. Check available sizes with the command   brother_ql_info list-label-sizes")

    qlr.exception_on_warning = True

    create_label(qlr, args.image, args.label_size, threshold=args.threshold, cut=args.cut, rotate=args.rotate)

    args.outfile.write(qlr.data)

def create_label(qlr, image, label_size, threshold=70, cut=True, **kwargs):

    label_specs = label_type_specs[label_size]
    dots_printable = label_specs['dots_printable']
    right_margin_dots = label_specs['right_margin_dots']
    device_pixel_width = qlr.get_pixel_width()
    rotate = kwargs.get('rotate', 'auto')

    if isinstance(image, Image.Image):
        im = image
    elif isinstance(image, (unicode, str)):
        im = Image.open(image)
    else:
        raise NotImplementedError("The image argument needs to be an Image() instance or the filename to an image.")

    if 'A' in im.mode:
        bg = Image.new("RGB", im.size, (255,255,255))
        bg.paste(im, im.split()[-1])
        im = bg

    if label_specs['kind'] == ENDLESS_LABEL:
        if rotate != 'auto' and int(rotate) != 0:
            im = im.rotate(int(rotate), expand=True)
        if im.size[0] != dots_printable[0]:
            hsize = int((dots_printable[0] / im.size[0]) * im.size[1])
            im = im.resize((dots_printable[0], hsize), Image.ANTIALIAS)
            logger.warning('Need to resize the image...')
        im = im.convert("L")
        if im.size[0] < device_pixel_width:
            new_im = Image.new("L", (device_pixel_width, im.size[1]), 255)
            new_im.paste(im, (device_pixel_width-im.size[0]-right_margin_dots, 0))
            im = new_im
    elif label_specs['kind'] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
        im = im.convert("L")
        if rotate == 'auto':
            if im.size[0] == dots_printable[1] and im.size[1] == dots_printable[0]:
                im = im.rotate(90, expand=True)
        elif int(rotate) != 0:
            im = im.rotate(rotate, expand=True)
        if im.size[0] != dots_printable[0] or im.size[1] != dots_printable[1]:
            sys.exit("Check your image dimensions. Expecting: " + str(dots_printable))
        new_im = Image.new("L", (device_pixel_width, dots_printable[1]), 255)
        new_im.paste(im, (device_pixel_width-im.size[0]-right_margin_dots, 0))
        im = new_im

    threshold = min(255, max(0, int(threshold/100.0 * 255))) # from percent to pixel val
    im = im.point(lambda x: 0 if x < threshold else 255, mode="1")

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
        if cut:
            qlr.add_autocut(True)
            qlr.add_cut_every(1)
    except BrotherQLUnsupportedCmd:
        pass
    try:
        qlr.dpi_600 = False
        qlr.cut_at_end = cut
        qlr.add_expanded_mode()
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_margins(label_specs['feed_margin'])
    try:
        qlr.add_compression(True)
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_raster_data(im)
    qlr.add_print()

if __name__ == "__main__":
    main()
