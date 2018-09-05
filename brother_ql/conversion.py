#!/usr/bin/env python

from __future__ import division, unicode_literals
from builtins import str

import logging

from PIL import Image
import PIL.ImageOps, PIL.ImageChops

from brother_ql.raster import BrotherQLRaster
from brother_ql.devicedependent import label_type_specs, ENDLESS_LABEL, DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL, right_margin_addition
from brother_ql import BrotherQLUnsupportedCmd
from brother_ql.image_trafos import filtered_hsv

logger = logging.getLogger(__name__)

logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)

def convert(qlr, images, label,  **kwargs):
    r"""Converts one or more images to a raster instruction file.

    :param qlr:
        An instance of the BrotherQLRaster class
    :type qlr: :py:class:`brother_ql.raster.BrotherQLRaster`
    :param images:
        The images to be converted. They can be filenames or instances of Pillow's Image.
    :type images: list(PIL.Image.Image) or list(str) images
    :param str label:
        Type of label the printout should be on.
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * **cut** (``bool``) --
          Enable cutting after printing the labels.
        * **dither** (``bool``) --
          Instead of applying a threshold to the pixel values, approximate grey tones with dithering.
        * **compress**
        * **red**
        * **rotate**
        * **dpi_600**
        * **hq**
        * **threshold**
    """
    label_specs = label_type_specs[label]

    dots_printable = label_specs['dots_printable']
    right_margin_dots = label_specs['right_margin_dots']
    right_margin_dots += right_margin_addition.get(qlr.model, 0)
    device_pixel_width = qlr.get_pixel_width()

    cut = kwargs.get('cut', True)
    dither = kwargs.get('dither', False)
    compress = kwargs.get('compress', False)
    red = kwargs.get('red', False)
    rotate = kwargs.get('rotate', 'auto')
    if rotate != 'auto': rotate = int(rotate)
    dpi_600 = kwargs.get('dpi_600', False)
    hq = kwargs.get('hq', True)
    threshold = kwargs.get('threshold', 70)
    threshold = 100.0 - threshold
    threshold = min(255, max(0, int(threshold/100.0 * 255)))

    if red and not qlr.two_color_support:
        raise BrotherQLUnsupportedCmd('Printing in red is not supported with the selected model.')

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

    for image in images:
        if isinstance(image, Image.Image):
            im = image
        else:
            try:
                im = Image.open(image)
            except:
                raise NotImplementedError("The image argument needs to be an Image() instance, the filename to an image, or a file handle.")

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

    return qlr.data
