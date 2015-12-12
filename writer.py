
import struct

import packbits
import numpy as np

from devicedependent import models, \
                            min_max_feed, \
                            min_max_length_dots, \
                            paper_dimensions, \
                            number_bytes_per_row, \
                            right_margin_addition

class QLRaster(object):

    def __init__(self, model='QL-500'):
        if model not in models:
            raise QLRasterUnknownModel()
        self.model = model
        self.data = b''
        self._pquality = 1
        self.page_number = 0
        self.cut_at_end = True
        self.dpi_600 = False
        self.compression = True

    def initialize(self):
        self.page_number = 0
        self.data += b'\x1B\x69\x61\x01' # mode setting (raster mode)
        self.data += b'\x00' * 200
        self.data += b'\x1B\x40' # init
        self.data += b'\x1B\x69\x61\x01' # mode setting (raster mode)

    @property
    def mtype(self): return self._mtype

    @property
    def mwidth(self): return self._mwidth

    @property
    def mlength(self): return self._mlength

    @property
    def pquality(self): return self._pquality

    @mtype.setter
    def mtype(self, value):
        self._mtype = bytes([value & 0xFF])

    @mwidth.setter
    def mwidth(self, value):
        self._mwidth = bytes([value & 0xFF])

    @mlength.setter
    def mlength(self, value):
        self._mlength = bytes([value & 0xFF])

    @pquality.setter
    def pquality(self, value):
        self._pquality = bytes([value & 0x01])

    def set_media_and_quality(self, rnumber):
        self.data += b'\x1B\x69\x7A'
        valid_flags = 0x80
        valid_flags |= (self._mtype is not None) << 1
        valid_flags |= (self._mwidth is not None) << 2
        valid_flags |= (self._mlength is not None) << 3
        valid_flags |= self._pquality << 6
        self.data += bytes([valid_flags])
        vals = [self._mtype, self._mwidth, self._mlength]
        self.data += b''.join(b'\x00' if val is None else val for val in vals)
        self.data += struct.pack('<L', rnumber)
        self.data += bytes([self.page_number == 0])
        self.data += b'\x00'
        # INFO:  media/quality (1B 69 7A) --> found! (payload: 8E 0A 3E 00 D2 00 00 00 00 00)

    def set_autocut(self, autocut = False):
        self.data += b'\x1B\x69\x4D'
        self.data += bytes([autocut << 6])

    def set_cut_every(self, n=1):
        self.data += b'\x1B\x69\x41'
        self.data += bytes([n & 0xFF])

    def set_expanded_mode(self):
        self.data += b'\x1B\x69\x4B'
        flags = 0x00
        flags |= self.cut_at_end << 3
        flags |= self.dpi_600 << 6
        self.data += bytes([flags])

    def set_margins(self, dots=0x23):
        self.data += b'\x1B\x69\x64'
        self.data += struct.pack('<H', dots)

    def set_compression(self, compression=True):
        self.compression = compression
        self.data += b'\x4D'
        self.data += bytes([compression << 1])

    def set_raster_data(self, np_array):
        """ np_array: numpy array of 1-bit values """
        np_array = np.fliplr(np_array)
        for row in np_array:
            self.data += b'\x67\x00'
            row = bytes(np.packbits(row))
            if self.compression:
                row = packbits.encode(row)
            self.data += bytes([len(row)])
            self.data += row

    def print(self, last_page=True):
        if last_page:
            self.data += b'\x1A'
        else:
            self.data += b'\x0C'

class QLRasterError(Exception): pass
class QLRasterUnknownModel(QLRasterError): pass

