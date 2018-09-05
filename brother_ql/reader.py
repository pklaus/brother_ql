#!/usr/bin/env python

import struct
import io
import logging
import sys

from PIL import Image
from PIL.ImageOps import colorize

from builtins import bytes

logger = logging.getLogger(__name__)

OPCODES = {
    # signature              name    following bytes   description
    b'\x00':                 ("preamble",       -1, "Preamble, 200-300x 0x00 to clear comamnd buffer"),
    b'\x4D':                 ("compression",     1, ""),
    b'\x67':                 ("raster",         -1, ""),
    b'\x77':                 ("2-color raster", -1, ""),
    b'\x0C':                 ("print",           0, "print intermediate page"),
    b'\x1A':                 ("print",           0, "print final page"),
    b'\x1b\x40':             ("init",            0, "initialization"),
    b'\x1b\x69\x61':         ("mode setting",    1, ""),
    b'\x1b\x69\x21':         ("automatic status",1, ""),
    b'\x1b\x69\x7A':         ("media/quality",  10, "print-media and print-quality"),
    b'\x1b\x69\x4D':         ("various",         1, "Auto cut flag in bit 7"),
    b'\x1b\x69\x41':         ("cut-every",       1, "cut every n-th page"),
    b'\x1b\x69\x4B':         ("expanded",        1, ""),
    b'\x1b\x69\x64':         ("margins",         2, ""),
    b'\x1b\x69\x55\x77\x01': ('amedia',        127, "Additional media information command"),
    b'\x1b\x69\x55\x4A':     ('jobid',          14, "Job ID setting command"),
    b'\x1b\x69\x58\x47':     ("request_config",  0, "Request transmission of .ini config file of printer"),
    b'\x1b\x69\x53':         ('status request',  0, "A status information request sent to the printer"),
    b'\x80\x20\x42':         ('status response',29, "A status response received from the printer"),
}

dot_widths = {
  62: 90*8,
}

RESP_ERROR_INFORMATION_1_DEF = {
  0: 'No media when printing',
  1: 'End of media (die-cut size only)',
  2: 'Tape cutter jam',
  3: 'Not used',
  4: 'Main unit in use (QL-560/650TD/1050)',
  5: 'Printer turned off',
  6: 'High-voltage adapter (not used)',
  7: 'Fan doesn\'t work (QL-1050/1060N)',
}

RESP_ERROR_INFORMATION_2_DEF = {
  0: 'Replace media error',
  1: 'Expansion buffer full error',
  2: 'Transmission / Communication error',
  3: 'Communication buffer full error (not used)',
  4: 'Cover opened while printing (Except QL-500)',
  5: 'Cancel key (not used)',
  6: 'Media cannot be fed (also when the media end is detected)',
  7: 'System error',
}

RESP_MEDIA_TYPES = {
  0x00: 'No media',
  0x0A: 'Continuous length tape',
  0x0B: 'Die-cut labels',
}

RESP_STATUS_TYPES = {
  0x00: 'Reply to status request',
  0x01: 'Printing completed',
  0x02: 'Error occurred',
  0x05: 'Notification',
  0x06: 'Phase change',
}

RESP_PHASE_TYPES = {
  0x00: 'Waiting to receive',
  0x01: 'Printing state',
}

RESP_BYTE_NAMES = [
  'Print head mark',
  'Size',
  'Fixed (B=0x42)',
  'Device dependent',
  'Device dependent',
  'Fixed (0=0x30)',
  'Fixed (0x00 or 0=0x30)',
  'Fixed (0x00)',
  'Error information 1',
  'Error information 2',
  'Media width',
  'Media type',
  'Fixed (0x00)',
  'Fixed (0x00)',
  'Reserved',
  'Mode',
  'Fixed (0x00)',
  'Media length',
  'Status type',
  'Phase type',
  'Phase number (high)',
  'Phase number (low)',
  'Notification number',
  'Reserved',
  'Reserved',
]

def hex_format(data):
    try: # Py3
        return ' '.join('{:02X}'.format(byte) for byte in data)
    except ValueError: # Py2
        return ' '.join('{:02X}'.format(ord(byte)) for byte in data)

def chunker(data, raise_exception=False):
    """
    Breaks data stream (bytes) into a list of bytes objects containing single instructions each.

    Logs warnings for unknown opcodes or raises an exception instead, if raise_exception is set to True.

    returns: list of bytes objects
    """
    instructions = []
    data = bytes(data)
    while True:
        if len(data) == 0: break
        try:
            opcode = match_opcode(data)
        except:
            msg = 'unknown opcode starting with {}...)'.format(hex_format(data[0:4]))
            if raise_exception:
                raise ValueError(msg)
            else:
                logger.warning(msg)
                data = data[1:]
                continue
        opcode_def = OPCODES[opcode]
        num_bytes = len(opcode)
        if opcode_def[1] > 0: num_bytes += opcode_def[1]
        if 'raster' in opcode_def[0]:
            num_bytes += data[2] + 2
        #payload = data[len(opcode):num_bytes]
        instructions.append(data[:num_bytes])
        data = data[num_bytes:]
    return instructions

def match_opcode(data):
    matching_opcodes = [opcode for opcode in OPCODES.keys() if data.startswith(opcode)]
    assert len(matching_opcodes) == 1
    return matching_opcodes[0]

def interpret_response(data):
    data = bytes(data)
    if len(data) < 32:
        raise NameError('Insufficient amount of data received', hex_format(data))
    if not data.startswith(b'\x80\x20\x42'):
        raise NameError("Printer response doesn't start with the usual header (80:20:42)", hex_format(data))
    for i, byte_name in enumerate(RESP_BYTE_NAMES):
        logger.debug('Byte %2d %24s %02X', i, byte_name+':', data[i])
    errors = []
    error_info_1 = data[8]
    error_info_2 = data[9]
    for error_bit in RESP_ERROR_INFORMATION_1_DEF:
        if error_info_1 & (1 << error_bit):
            logger.error('Error: ' + RESP_ERROR_INFORMATION_1_DEF[error_bit])
            errors.append(RESP_ERROR_INFORMATION_1_DEF[error_bit])
    for error_bit in RESP_ERROR_INFORMATION_2_DEF:
        if error_info_2 & (1 << error_bit):
            logger.error('Error: ' + RESP_ERROR_INFORMATION_2_DEF[error_bit])
            errors.append(RESP_ERROR_INFORMATION_2_DEF[error_bit])

    media_width  = data[10]
    media_length = data[17]

    media_type = data[11]
    if media_type in RESP_MEDIA_TYPES:
        media_type = RESP_MEDIA_TYPES[media_type]
        logger.debug("Media type: %s", media_type)
    else:
        logger.error("Unknown media type %02X", media_type)

    status_type = data[18]
    if status_type in RESP_STATUS_TYPES:
        status_type = RESP_STATUS_TYPES[status_type]
        logger.debug("Status type: %s", status_type)
    else:
        logger.error("Unknown status type %02X", status_type)

    phase_type = data[19]
    if phase_type in RESP_PHASE_TYPES:
        phase_type = RESP_PHASE_TYPES[phase_type]
        logger.debug("Phase type: %s", phase_type)
    else:
        logger.error("Unknown phase type %02X", phase_type)

    response = {
      'status_type': status_type,
      'phase_type': phase_type,
      'media_type': media_type,
      'media_width': media_width,
      'media_length': media_length,
      'errors': errors,
    }
    return response


def merge_specific_instructions(chunks, join_preamble=True, join_raster=True):
    """
    Process a list of instructions by merging subsequent instuctions with
    identical opcodes into "large instructions".
    """
    new_instructions = []
    last_opcode = None
    instruction_buffer = b''
    for instruction in chunks:
        opcode = match_opcode(instruction)
        if   join_preamble and OPCODES[opcode][0] == 'preamble' and last_opcode == 'preamble':
            instruction_buffer += instruction
        elif join_raster   and 'raster' in OPCODES[opcode][0] and 'raster' in last_opcode:
            instruction_buffer += instruction
        else:
            if instruction_buffer:
                new_instructions.append(instruction_buffer)
            instruction_buffer = instruction
        last_opcode = OPCODES[opcode][0]
    if instruction_buffer:
        new_instructions.append(instruction_buffer)
    return new_instructions

class BrotherQLReader(object):
    DEFAULT_FILENAME_FMT = 'label{counter:04d}.png'

    def __init__(self, brother_file):
        if type(brother_file) in (str,):
            brother_file = io.open(brother_file, 'rb')
        self.brother_file = brother_file
        self.mwidth, self.mheight = None, None
        self.raster_no = None
        self.black_rows = []
        self.red_rows = []
        self.compression = False
        self.page_counter = 1
        self.two_color_printing = False
        self.cut_at_end = False
        self.high_resolution_printing = False
        self.filename_fmt = self.DEFAULT_FILENAME_FMT

    def analyse(self):
        instructions = self.brother_file.read()
        for instruction in chunker(instructions):
            for opcode in OPCODES.keys():
                if instruction.startswith(opcode):
                    opcode_def = OPCODES[opcode]
                    if opcode_def[0] == 'init':
                        self.mwidth, self.mheight = None, None
                        self.raster_no = None
                        self.black_rows = []
                        self.red_rows = []
                    payload = instruction[len(opcode):]
                    logger.info(" {} ({}) --> found! (payload: {})".format(opcode_def[0], hex_format(opcode), hex_format(payload)))
                    if opcode_def[0] == 'compression':
                        self.compression = payload[0] == 0x02
                    if 'raster' in opcode_def[0]:
                        rpl = bytes(payload[2:]) # raster payload
                        if self.compression:
                            row = bytes()
                            index = 0
                            while True:
                                num = rpl[index]
                                if num & 0x80:
                                    num = num - 0x100
                                if num < 0:
                                    num = -num + 1
                                    row += bytes([rpl[index+1]] * num)
                                    index += 2
                                else:
                                    num = num + 1
                                    row += rpl[index+1:index+1+num]
                                    index += 1 + num
                                if index >= len(rpl): break
                        else:
                            row = rpl
                        if opcode_def[0] == 'raster':
                            self.black_rows.append(row)
                        else: # 2-color
                            if   payload[0] == 0x01:
                                self.black_rows.append(row)
                            elif payload[0] == 0x02:
                                self.red_rows.append(row)
                            else:
                                raise NotImplementedError("color: 0x%x" % payload[0])
                    if opcode_def[0] == 'expanded':
                        self.two_color_printing = bool(payload[0] & (1 << 0))
                        self.cut_at_end = bool(payload[0] & (1 << 3))
                        self.high_resolution_printing = bool(payload[0] & (1 << 6))
                    if opcode_def[0] == 'media/quality':
                        self.raster_no = struct.unpack('<L', payload[4:8])[0]
                        self.mwidth = instruction[len(opcode) + 2]
                        self.mlength = instruction[len(opcode) + 3]*256
                        fmt = " media width: {} mm, media length: {} mm, raster no: {} rows"
                        logger.info(fmt.format(self.mwidth, self.mlength, self.raster_no))
                    if opcode_def[0] == 'print':
                        logger.info("Len of black rows: %d", len(self.black_rows))
                        logger.info("Len of red   rows: %d", len(self.red_rows))
                        def get_im(rows):
                            if not len(rows): return None
                            size = (len(rows[0])*8, len(rows))
                            data = bytes(b''.join(rows))
                            data = bytes([2**8 + ~byte for byte in data]) # invert b/w
                            im = Image.frombytes("1", size, data, decoder_name='raw')
                            return im
                        im_black, im_red = (get_im(rows) for rows in (self.black_rows, self.red_rows))
                        if not self.two_color_printing:
                            im = im_black
                        else:
                            im_black = im_black.convert("RGBA")
                            im_red = im_red.convert("L")
                            im_red = colorize(im_red, (255, 0, 0), (255, 255, 255))
                            im_red = im_red.convert("RGBA")
                            pixdata_black = im_black.load()
                            width, height = im_black.size
                            for y in range(height):
                                for x in range(width):
                                    # replace "white" with "transparent"
                                    if pixdata_black[x, y] == (255, 255, 255, 255):
                                        pixdata_black[x, y] = (255, 255, 255, 0)
                            im_red.paste(im_black, (0, 0), im_black)
                            im = im_red
                        im = im.transpose(Image.FLIP_LEFT_RIGHT)
                        img_name = self.filename_fmt.format(counter=self.page_counter)
                        im.save(img_name)
                        print('Page saved as {}'.format(img_name))
                        self.page_counter += 1
