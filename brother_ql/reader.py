#!/usr/bin/env python

import struct
import io
import logging
import sys

from PIL import Image
import numpy as np

from builtins import bytes

logger = logging.getLogger(__name__)

OPCODES = {
    # signature              name    following bytes   description
    b'\x00':                 ("preamble",       -1, "Preamble, 200-300x 0x00 to clear comamnd buffer"),
    b'\x4D':                 ("compression",     1, ""),
    b'\x67':                 ("raster",         -1, ""),
    b'\x0C':                 ("print",           0, "print intermediate page"),
    b'\x1A':                 ("print",           0, "print final page"),
    b'\x1b\x40':             ("init",            0, "initialization"),
    b'\x1b\x69\x61':         ("mode setting",    1, ""),
    b'\x1b\x69\x7A':         ("media/quality",  10, "print-media and print-quality"),
    b'\x1b\x69\x4D':         ("various",         1, "Auto cut flag in bit 7"),
    b'\x1b\x69\x41':         ("cut-every",       1, "cut every n-th page"),
    b'\x1b\x69\x4B':         ("expanded",        1, ""),
    b'\x1b\x69\x64':         ("margins",         2, ""),
    b'\x1b\x69\x55\x77\x01': ('amedia',        127, "Additional media information command"),
    b'\x1b\x69\x55\x4A':     ('jobid',          14, "Job ID setting command"),
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
  7: 'Fan doesn’t work (QL-1050/1060N)',
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
        if opcode_def[0] == 'raster':
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
    assert len(data) >= 32
    assert data.startswith(b'\x80\x20\x42')
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
        elif join_raster   and OPCODES[opcode][0] == 'raster'   and last_opcode == 'raster':
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

    def __init__(self, brother_file):
        if type(brother_file) in (str,):
            brother_file = io.open(brother_file, 'rb')
        self.brother_file = brother_file
        self.mwidth, self.mheight = None, None
        self.raster_no = None
        self.rows = []
        self.compression = False
        self.page = 1

    def analyse(self):
        instructions = self.brother_file.read()
        for instruction in chunker(instructions):
            for opcode in OPCODES.keys():
                if instruction.startswith(opcode):
                    opcode_def = OPCODES[opcode]
                    if opcode_def[0] == 'init':
                        self.mwidth, self.mheight = None, None
                        self.raster_no = None
                        self.rows = []
                    payload = instruction[len(opcode):]
                    logger.info(" {} ({}) --> found! (payload: {})".format(opcode_def[0], hex_format(opcode), hex_format(payload)))
                    if opcode_def[0] == 'compression':
                        self.compression = payload[0] == 0x02
                    if opcode_def[0] == 'raster':
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
                        self.rows.append(row)
                    if opcode_def[0] == 'media/quality':
                        self.raster_no = struct.unpack('<L', payload[4:8])[0]
                        self.mwidth = instruction[len(opcode) + 2]
                        self.mlength = instruction[len(opcode) + 3]*256
                        fmt = " media width: {}mm, media length: {}mm, raster no: {}dots"
                        logger.info(fmt.format(self.mwidth, self.mlength, self.raster_no))
                    if opcode_def[0] == 'print':
                        size = (len(self.rows[0])*8, len(self.rows))
                        data = bytes(b''.join(self.rows))
                        data = bytes([2**8 + ~byte for byte in data]) # invert b/w
                        im = Image.frombytes("1", size, data, decoder_name='raw')
                        im = im.transpose(Image.FLIP_LEFT_RIGHT)
                        img_name = 'page{:04d}.png'.format(self.page)
                        im.save(img_name)
                        print('Page saved as {}'.format(img_name))
                        self.page += 1
