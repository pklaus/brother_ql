"""
This module contains the implementation of the raster language
of the Brother QL-series label printers according to their
documentation and to reverse engineering efforts.

The central piece of code in this module is the class
:py:class:`BrotherQLRaster`.
"""

from builtins import bytes

import struct
import logging

import packbits
from PIL import Image
import io

from brother_ql.models import ModelsManager
from .devicedependent import models, \
                             min_max_feed, \
                             min_max_length_dots, \
                             number_bytes_per_row, \
                             compressionsupport, \
                             cuttingsupport, \
                             expandedmode, \
                             two_color_support, \
                             modesetting

from . import BrotherQLError, BrotherQLUnsupportedCmd, BrotherQLUnknownModel, BrotherQLRasterError

try:
    from io import BytesIO
except: # Py2
    from cStringIO import StringIO as BytesIO

logger = logging.getLogger(__name__)

class BrotherQLRaster(object):

    """
    This class facilitates the creation of a complete set
    of raster instructions by adding them one after the other
    using the methods of the class. Each method call is adding
    instructions to the member variable :py:attr:`data`.

    Instatiate the class by providing the printer
    model as argument.

    :param str model: Choose from the list of available models.

    :ivar bytes data: The resulting bytecode with all instructions.
    :ivar bool exception_on_warning: If set to True, an exception is raised if trying to add instruction which are not supported on the selected model. If set to False, the instruction is simply ignored and a warning sent to logging/stderr.
    """

    def __init__(self, model='QL-500'):
        if model not in models:
            raise BrotherQLUnknownModel()
        self.model = model
        self.data = b''
        self._pquality = True
        self.page_number = 0
        self.cut_at_end = True
        self.dpi_600 = False
        self.two_color_printing = False
        self._compression = False
        self.exception_on_warning = False

        self.num_invalidate_bytes = 200
        for m in ModelsManager().iter_elements():
            if self.model == m.identifier:
                self.num_invalidate_bytes = m.num_invalidate_bytes
                break

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

    def _unsupported(self, problem):
        """
        Raises BrotherQLUnsupportedCmd if
        exception_on_warning is set to True.
        Issues a logger warning otherwise.

        :raises BrotherQLUnsupportedCmd:
        """
        self._warn(problem, kind=BrotherQLUnsupportedCmd)

    @property
    def two_color_support(self):
        return self.model in two_color_support

    def add_initialize(self):
        self.page_number = 0
        self.data += b'\x1B\x40' # ESC @

    def add_status_information(self):
        """ Status Information Request """
        self.data += b'\x1B\x69\x53' # ESC i S

    def add_switch_mode(self):
        """
        Switch dynamic command mode
        Switch to the raster mode on the printers that support
        the mode change (others are in raster mode already).
        """
        if self.model not in modesetting:
            self._unsupported("Trying to switch the operating mode on a printer that doesn't support the command.")
            return
        self.data += b'\x1B\x69\x61\x01' # ESC i a

    def add_invalidate(self):
        """ clear command buffer """
        self.data += b'\x00' * self.num_invalidate_bytes

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
        self._pquality = bool(value)

    def add_media_and_quality(self, rnumber):
        self.data += b'\x1B\x69\x7A' # ESC i z
        valid_flags = 0x80
        valid_flags |= (self._mtype is not None) << 1
        valid_flags |= (self._mwidth is not None) << 2
        valid_flags |= (self._mlength is not None) << 3
        valid_flags |= self._pquality << 6
        self.data += bytes([valid_flags])
        vals = [self._mtype, self._mwidth, self._mlength]
        self.data += b''.join(b'\x00' if val is None else val for val in vals)
        self.data += struct.pack('<L', rnumber)
        self.data += bytes([0 if self.page_number == 0 else 1])
        self.data += b'\x00'
        # INFO:  media/quality (1B 69 7A) --> found! (payload: 8E 0A 3E 00 D2 00 00 00 00 00)

    def add_autocut(self, autocut = False):
        if self.model not in cuttingsupport:
            self._unsupported("Trying to call add_autocut with a printer that doesn't support it")
            return
        self.data += b'\x1B\x69\x4D' # ESC i M
        self.data += bytes([autocut << 6])

    def add_cut_every(self, n=1):
        if self.model not in cuttingsupport:
            self._unsupported("Trying to call add_cut_every with a printer that doesn't support it")
            return
        self.data += b'\x1B\x69\x41' # ESC i A
        self.data += bytes([n & 0xFF])

    def add_expanded_mode(self):
        if self.model not in expandedmode:
            self._unsupported("Trying to set expanded mode (dpi/cutting at end) on a printer that doesn't support it")
            return
        if self.two_color_printing and not self.two_color_support:
            self._unsupported("Trying to set two_color_printing in expanded mode on a printer that doesn't support it.")
            return
        self.data += b'\x1B\x69\x4B' # ESC i K
        flags = 0x00
        flags |= self.cut_at_end << 3
        flags |= self.dpi_600 << 6
        flags |= self.two_color_printing << 0
        self.data += bytes([flags])

    def add_margins(self, dots=0x23):
        self.data += b'\x1B\x69\x64' # ESC i d
        self.data += struct.pack('<H', dots)

    def add_compression(self, compression=True):
        """
        Add an instruction enabling or disabling compression for the transmitted raster image lines.
        Not all models support compression. If the specific model doesn't support it but this method
        is called trying to enable it, either a warning is set or an exception is raised depending on
        the value of :py:attr:`exception_on_warning`

        :param bool compression: Whether compression should be on or off
        """
        if self.model not in compressionsupport:
            self._unsupported("Trying to set compression on a printer that doesn't support it")
            return
        self._compression = compression
        self.data += b'\x4D' # M
        self.data += bytes([compression << 1])

    def get_pixel_width(self):
        try:
            nbpr = number_bytes_per_row[self.model]
        except:
            nbpr = number_bytes_per_row['default']
        return nbpr*8

    def add_raster_data(self, image, second_image=None):
        """
        Add the image data to the instructions.
        The provided image has to be binary (every pixel
        is either black or white).

        :param PIL.Image.Image image: The image to be converted and added to the raster instructions
        :param PIL.Image.Image second_image: A second image with a separate color layer (red layer for the QL-800 series)
        """
        logger.debug("raster_image_size: {0}x{1}".format(*image.size))
        if image.size[0] != self.get_pixel_width():
            fmt = 'Wrong pixel width: {}, expected {}'
            raise BrotherQLRasterError(fmt.format(image.size[0], self.get_pixel_width()))
        images = [image]
        if second_image:
            if image.size != second_image.size:
                fmt = "First and second image don't have the same dimesions: {} vs {}."
                raise BrotherQLRasterError(fmt.format(image.size, second_image.size))
            images.append(second_image)
        frames = []
        for image in images:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
            image = image.convert("1")
            frames.append(bytes(image.tobytes(encoder_name='raw')))
        frame_len = len(frames[0])
        row_len = images[0].size[0]//8
        start = 0
        file_str = BytesIO()
        while start + row_len <= frame_len:
            for i, frame in enumerate(frames):
                row = frame[start:start+row_len]
                if self._compression:
                    row = packbits.encode(row)
                translen = len(row) # number of bytes to be transmitted
                if self.model.startswith('PT'):
                    file_str.write(b'\x47')
                    file_str.write(bytes([translen%256, translen//256]))
                else:
                    if second_image:
                        file_str.write(b'\x77\x01' if i == 0 else b'\x77\x02')
                    else:
                        file_str.write(b'\x67\x00')
                    file_str.write(bytes([translen]))
                file_str.write(row)
            start += row_len
        self.data += file_str.getvalue()

    def add_print(self, last_page=True):
        if last_page:
            self.data += b'\x1A' # 0x1A = ^Z = SUB; here: EOF = End of File
        else:
            self.data += b'\x0C' # 0x0C = FF  = Form Feed
