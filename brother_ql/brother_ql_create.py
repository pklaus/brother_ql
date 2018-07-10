#!/usr/bin/env python

from __future__ import division

import sys, argparse, logging

from PIL import Image
import PIL.ImageOps, PIL.ImageChops

from brother_ql.raster import BrotherQLRaster
from brother_ql.devicedependent import models, label_type_specs, ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL, right_margin_addition
from brother_ql import BrotherQLError, BrotherQLUnsupportedCmd, BrotherQLUnknownModel
from brother_ql.image_trafos import filtered_hsv

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
    parser.add_argument('--dither', '-d', action='store_true', help='Enable dithering when converting the image to b/w. If set, --threshold is meaningless.')
    parser.add_argument('--compress', '-c', action='store_true', help='Enable compression (if available with the model). Takes more time but results in smaller file size.')
    parser.add_argument('--red', action='store_true', help='Create a label to be printed on black/red/white tape (only with QL-8xx series on DK-22251 labels). You must use this option when printing on black/red tape, even when not printing red.')
    parser.add_argument('--600dpi', action='store_true', dest='dpi_600', help='Print with 600x300 dpi available on some models. Provide your image as 600x600 dpi; perpendicular to the feeding the image will be resized to 300dpi.')
    parser.add_argument('--lq', action='store_false', dest='hq', help='Print with low quality (faster). Default is high quality.')
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

    create_label(qlr, args.image, args.label_size, threshold=args.threshold, cut=args.cut, rotate=args.rotate, dither=args.dither, compress=args.compress, red=args.red, dpi_600=args.dpi_600, hq=args.hq)

    args.outfile.write(qlr.data)

def create_label(qlr, image, label_size, threshold=70, cut=True, dither=False, compress=False, red=False, **kwargs):

    label_specs = label_type_specs[label_size]
    dots_printable = label_specs['dots_printable']
    right_margin_dots = label_specs['right_margin_dots']
    right_margin_dots += right_margin_addition.get(qlr.model, 0)
    device_pixel_width = qlr.get_pixel_width()
    rotate = kwargs.get('rotate', 'auto')
    if rotate != 'auto': rotate = int(rotate)
    dpi_600 = kwargs.get('dpi_600', False)
    hq = kwargs.get('hq', True)

    threshold = 100.0 - threshold
    threshold = min(255, max(0, int(threshold/100.0 * 255))) # from percent to pixel val

    if red and not qlr.two_color_support:
        raise BrotherQLUnsupportedCmd('Printing in red is not supported with the selected model.')

    if isinstance(image, Image.Image):
        im = image
    elif isinstance(image, (unicode, str)):
        im = Image.open(image)
    else:
        raise NotImplementedError("The image argument needs to be an Image() instance or the filename to an image.")

    if im.mode.endswith('A'):
        # place in front of white background and get red of transparency
        bg = Image.new("RGB", im.size, (255,255,255))
        bg.paste(im, im.split()[-1])
        im = bg
    elif im.mode == "P":
        # Convert GIF ("P") to RGB
        im = im.convert("RGB" if red else "L")
    elif im.mode == "L" and red:
        # Convert greyscale to RGB if printing on black/red tape
        im = im.convert("RGB")

    if dpi_600:
        dots_expected = [el*2 for el in dots_printable]
    else:
        dots_expected = dots_printable

    if label_specs['kind'] == ENDLESS_LABEL:
        if rotate not in ('auto', 0):
            im = im.rotate(rotate, expand=True)
        if dpi_600:
            im = im.resize((im.size[0]//2, im.size[1]))
        if im.size[0] != dots_printable[0]:
            hsize = int((dots_printable[0] / im.size[0]) * im.size[1])
            im = im.resize((dots_printable[0], hsize), Image.ANTIALIAS)
            logger.warning('Need to resize the image...')
        if im.size[0] < device_pixel_width:
            new_im = Image.new(im.mode, (device_pixel_width, im.size[1]), (255,)*len(im.mode))
            new_im.paste(im, (device_pixel_width-im.size[0]-right_margin_dots, 0))
            im = new_im
    elif label_specs['kind'] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
        if rotate == 'auto':
            if im.size[0] == dots_expected[1] and im.size[1] == dots_expected[0]:
                im = im.rotate(90, expand=True)
        elif rotate != 0:
            im = im.rotate(rotate, expand=True)
        if im.size[0] != dots_expected[0] or im.size[1] != dots_expected[1]:
            raise ValueError("Bad image dimensions: %s. Expecting: %s." % (im.size, dots_expected))
        if dpi_600:
            im = im.resize((im.size[0]//2, im.size[1]))
        new_im = Image.new(im.mode, (device_pixel_width, dots_expected[1]), (255,)*len(im.mode))
        new_im.paste(im, (device_pixel_width-im.size[0]-right_margin_dots, 0))
        im = new_im

    if red:
        filter_h = lambda h: 255 if (h <  40 or h > 210) else 0
        filter_s = lambda s: 255 if s > 100 else 0
        filter_v = lambda v: 255 if v >  80 else 0
        red_im = filtered_hsv(im, filter_h, filter_s, filter_v)
        red_im = red_im.convert("L")
        red_im = PIL.ImageOps.invert(red_im)
        red_im = red_im.point(lambda x: 0 if x < threshold else 255, mode="1")

        filter_h = lambda h: 255
        filter_s = lambda s: 255
        filter_v = lambda v: 255 if v <  80 else 0
        black_im = filtered_hsv(im, filter_h, filter_s, filter_v)
        black_im = black_im.convert("L")
        black_im = PIL.ImageOps.invert(black_im)
        black_im = black_im.point(lambda x: 0 if x < threshold else 255, mode="1")
        black_im = PIL.ImageChops.subtract(black_im, red_im)
    else:
        im = im.convert("L")
        im = PIL.ImageOps.invert(im)

        if dither:
            im = im.convert("1", dither=Image.FLOYDSTEINBERG)
        else:
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
    qlr.pquality = int(hq)
    qlr.add_media_and_quality(im.size[1])
    try:
        if cut:
            qlr.add_autocut(True)
            qlr.add_cut_every(1)
    except BrotherQLUnsupportedCmd:
        pass
    try:
        qlr.dpi_600 = dpi_600
        qlr.cut_at_end = cut
        qlr.two_color_printing = True if red else False
        qlr.add_expanded_mode()
    except BrotherQLUnsupportedCmd:
        pass
    qlr.add_margins(label_specs['feed_margin'])
    try:
        if compress: qlr.add_compression(True)
    except BrotherQLUnsupportedCmd:
        pass
    if red:
        qlr.add_raster_data(black_im, red_im)
    else:
        qlr.add_raster_data(im)
    qlr.add_print()

if __name__ == "__main__":
    main()
