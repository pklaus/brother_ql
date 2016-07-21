
import struct
import logging

import packbits
import numpy as np

from .devicedependent import models, \
                             min_max_feed, \
                             min_max_length_dots, \
                             paper_dimensions, \
                             number_bytes_per_row, \
                             right_margin_addition, \
                             compressionsupport, \
                             cuttingsupport, \
                             expandedmode, \
                             modesetting

from . import BrotherQLError, BrotherQLUnsupportedCmd, BrotherQLUnknownModel, BrotherQLRasterError

logger = logging.getLogger(__name__)

class BrotherQLRaster(object):

    def __init__(self, model='QL-500'):
        if model not in models:
            raise BrotherQLUnknownModel()
        self.model = model
        self.data = b''
        self._pquality = 1
        self.page_number = 0
        self.cut_at_end = True
        self.dpi_600 = False
        self._compression = False
        self.exception_on_warning = False

    def _warn(self, problem, kind=BrotherQLRasterError):
        """
        Logs the warning message `problem` or raises a
        `BrotherQLRasterError` exception (changeable via `kind`)
        if `self.exception_on_warning` is set to True.

        :raises BrotherQLRasterError: Or other exception \
            set via the `kind` keyword argument.
        """
        if self.exception_on_warning:
            raise kind(problem)
        else:
            logger.warning(problem)

    def unsupported(self, problem):
        """
        Raises BrotherQLUnsupportedCmd if
        exception_on_warning is set to True.
        Issues a logger warning otherwise.

        :raises BrotherQLUnsupportedCmd:
        """
        self._warn(problem, kind=BrotherQLUnsupportedCmd)

    def add_initialize(self):
        self.page_number = 0
        self.data += b'\x1B\x40' # init

    def add_status_information(self):
        """ Status Information Request """
        self.data += b'\x1B\x69\x53'

    def add_switch_mode(self):
        """
        Switch dynamic command mode
        Switch to the raster mode on the printers that support
        the mode change (others are in raster mode already).
        """
        if self.model not in modesetting:
            self.unsupported("Trying to switch the operating mode on a printer that doesn't support the command.")
            return
        self.data += b'\x1B\x69\x61\x01'

    def add_invalidate(self):
        """ clear command buffer """
        self.data += b'\x00' * 200

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

    def add_media_and_quality(self, rnumber):
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

    def add_autocut(self, autocut = False):
        if self.model not in cuttingsupport:
            self.unsupported("Trying to call add_autocut with a printer that doesn't support it")
            return
        self.data += b'\x1B\x69\x4D'
        self.data += bytes([autocut << 6])

    def add_cut_every(self, n=1):
        if self.model not in cuttingsupport:
            self.unsupported("Trying to call add_cut_every with a printer that doesn't support it")
            return
        self.data += b'\x1B\x69\x41'
        self.data += bytes([n & 0xFF])

    def add_expanded_mode(self):
        if self.model not in expandedmode:
            self.unsupported("Trying to set expanded mode (dpi/cutting at end) on a printer that doesn't support it")
            return
        self.data += b'\x1B\x69\x4B'
        flags = 0x00
        flags |= self.cut_at_end << 3
        flags |= self.dpi_600 << 6
        self.data += bytes([flags])

    def add_margins(self, dots=0x23):
        self.data += b'\x1B\x69\x64'
        self.data += struct.pack('<H', dots)

    def add_compression(self, compression=True):
        if self.model not in compressionsupport:
            self.unsupported("Trying to set compression on a printer that doesn't support it")
            return
        self._compression = compression
        self.data += b'\x4D'
        self.data += bytes([compression << 1])

    def get_pixel_width(self):
        try:
            nbpr = number_bytes_per_row[self.model]
        except:
            nbpr = number_bytes_per_row['default']
        return nbpr*8

    def add_raster_data(self, np_array):
        """ np_array: numpy array of 1-bit values """
        np_array = np.fliplr(np_array)
        logger.info("raster_image_size: {1}x{0}".format(*np_array.shape))
        if np_array.shape[1] != self.get_pixel_width():
            fmt = 'Wrong pixel width: {}, expected {}'
            raise BrotherQLRasterError(fmt.format(np_array.shape[0], self.get_pixel_width()))
        for row in np_array:
            self.data += b'\x67\x00'
            row = bytes(np.packbits(row))
            if self._compression:
                row = packbits.encode(row)
            self.data += bytes([len(row)])
            self.data += row

    def add_print(self, last_page=True):
        if last_page:
            self.data += b'\x1A'
        else:
            self.data += b'\x0C'
