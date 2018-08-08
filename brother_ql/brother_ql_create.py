#!/usr/bin/env python

import sys, argparse, logging

from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.devicedependent import label_type_specs

try:
    stdout = sys.stdout.buffer
except:
    stdout = sys.stdout

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
    convert(qlr, [image], label_size, threshold=threshold, cut=cut, dither=dither, compress=compress, red=red, **kwargs)

if __name__ == "__main__":
    main()
