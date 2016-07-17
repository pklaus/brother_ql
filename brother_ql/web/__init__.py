#!/usr/bin/env python

"""
This is a web server to print labels.

Go to [/api/print/text/Your_Text](/api/print/text/)
to print a label (replace Your_Text with your text).
"""

import sys, logging, socket, os, subprocess

from bottle import run, route, response, request
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import markdown

from brother_ql.raster import BrotherQLRaster

logger = logging.getLogger(__name__)

# globals:
DEBUG = False

FONTS = None

DEFAULT_FONT = None

DEFAULT_FONTS = [
  {'family': 'Minion Pro',      'style': 'Semibold'},
  {'family': 'Linux Libertine', 'style': 'Regular'},
  {'family': 'DejaVu Serif',    'style': 'Book'},
]

@route('/')
def index():
    return markdown.markdown(__doc__)

def get_fonts(folder=None):
    """
    Scan a folder (or the system) for .ttf / .otf fonts and
    return a dictionary of the structure  family -> style -> file path
    """
    fonts = {}
    if folder:
        cmd = ['fc-scan', '--format', '"%{file}:%{family}:style=%{style}\n"', folder]
    else:
        cmd = ['fc-list', ':', 'file', 'family', 'style']
    for line in subprocess.check_output(cmd).decode('utf-8').split("\n"):
        logger.debug(line)
        line.strip()
        if not line: continue
        if 'otf' not in line and 'ttf' not in line: continue
        parts = line.split(':')
        path = parts[0]
        families = parts[1].strip().split(',')
        styles = parts[2].split('=')[1].split(',')
        if len(families) == 1 and len(styles) > 1:
            families = [families[0]] * len(styles)
        elif len(families) > 1 and len(styles) == 1:
            styles = [styles[0]] * len(families)
        if len(families) != len(styles):
            if DEBUG:
                print("Problem with this font:")
                print(line)
            continue
        for i in range(len(families)):
            try: fonts[families[i]]
            except: fonts[families[i]] = dict()
            fonts[families[i]][styles[i]] = path
            if DEBUG:
                print("Added this font:")
                print(families[i], styles[i], path)
    return fonts

@route('/api/print/text')
@route('/api/print/text/')
@route('/api/print/text/<content>')
def print_text(content=None):
    """
    More possible parameters:
    - alignment
    """

    return_dict = {'success': False}

    if content is None:
        return_dict['error'] = 'Please provide the text for the label'
        return return_dict

    threshold = 170
    fontsize = 100
    width = 720
    margin = 0
    height = 100 + 2*margin
    model = 'QL-710W'
    host = '192.168.178.32'
    port = 9100

    try:
        font_family = request.query.get('font_family')
        font_style  = request.query.get('font_style')
        if font_family is None:
            font_family = DEFAULT_FONT['family']
            font_style =  DEFAULT_FONT['style']
        if font_style is None:
            font_style =  'Regular'
        font_path = FONTS[font_family][font_style]
    except KeyError:
        return_dict['error'] = "Couln't find the font & style"
        return return_dict

    im = Image.new('L', (width, height), 'white')
    draw = ImageDraw.Draw(im)
    im_font = ImageFont.truetype(font_path, fontsize)
    textsize = draw.textsize(content, font=im_font)
    vertical_offset = (height - textsize[1])//2
    horizontal_offset = max((width - textsize[0])//2, 0)
    if 'ttf' in font_path: vertical_offset -= 10
    offset = horizontal_offset, vertical_offset
    if DEBUG: print("Offset: {}".format(offset))
    draw.text(offset, content, (0), font=im_font)
    if DEBUG: im.save('sample-out.png')
    arr = np.asarray(im, dtype=np.uint8)
    arr.flags.writeable = True
    white_idx = arr[:,:] <  threshold
    black_idx = arr[:,:] >= threshold
    arr[white_idx] = 1
    arr[black_idx] = 0

    qlr = BrotherQLRaster(model)
    qlr.add_switch_mode()
    qlr.add_invalidate()
    qlr.add_initialize()
    qlr.add_mode()
    qlr.mtype = 0x0A
    qlr.mwidth = 62
    qlr.mlength = 0
    qlr.add_media_and_quality(im.size[1])
    qlr.add_autocut(True)
    qlr.add_cut_every(1)
    qlr.dpi_600 = False
    qlr.cut_at_end = True
    qlr.add_expanded_mode()
    qlr.add_margins()
    qlr.add_compression(True)
    qlr.add_raster_data(arr)
    qlr.add_print()

    if not DEBUG:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.connect((host, port))
        s.send(qlr.data)
        s.close()

    return_dict['success'] = True
    if DEBUG: return_dict['data'] = str(qlr.data)
    return return_dict

def main():
    global DEBUG, FONTS, DEFAULT_FONT
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8013)
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x.upper()), default='WARNING')
    parser.add_argument('--font-folder', help='folder for additional .ttf/.otf fonts')
    args = parser.parse_args()

    DEBUG = args.loglevel == logging.DEBUG
    logging.basicConfig(level=args.loglevel)

    FONTS = get_fonts()
    if args.font_folder:
        FONTS.update(get_fonts(args.font_folder))

    for font in DEFAULT_FONTS:
        try:
            FONTS[font['family']][font['style']]
            DEFAULT_FONT = font
            logger.debug("Selected the following default font: {}".format(font))
            break
        except: pass
    if DEFAULT_FONT is None:
        sys.stderr.write('Could not find any of the default fonts')
        sys.exit()

    run(host='localhost', port=args.port, debug=args.loglevel==logging.DEBUG)

if __name__ == "__main__":
    main()
