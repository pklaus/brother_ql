from attr import attrs, attrib
from typing import Tuple

import copy

from brother_ql.helpers import ElementsManager

@attrs
class Model(object):
    """
    This class represents a printer model. All specifics of a certain model
    and the opcodes it supports should be contained in this class.
    """
    #: A string identifier given to each model implemented. Eg. 'QL-500'.
    identifier = attrib(type=str)
    #: Minimum and maximum number of rows or 'dots' that can be printed.
    #: Together with the dpi this gives the minimum and maximum length
    #: for continuous tape printing.
    min_max_length_dots = attrib(type=Tuple[int, int])
    #: The minimum and maximum amount of feeding a label
    min_max_feed = attrib(type=Tuple[int, int], default=(35, 1500))
    number_bytes_per_row = attrib(type=int, default=90)
    #: The required additional offset from the right side
    additional_offset_r = attrib(type=int, default=0)
    #: Support for the 'mode setting' opcode
    mode_setting = attrib(type=bool, default=True)
    #: Model has a cutting blade to automatically cut labels
    cutting = attrib(type=bool, default=True)
    #: Model has support for the 'expanded mode' opcode.
    #: (So far, all models that have cutting support do).
    expanded_mode = attrib(type=bool, default=True)
    #: Model has support for compressing the transmitted raster data.
    #: Some models with only USB connectivity don't support compression.
    compression = attrib(type=bool, default=True)
    #: Support for two color printing (black/red/white)
    #: available only on some newer models.
    two_color = attrib(type=bool, default=False)

    @property
    def name(self):
        return self.identifier

ALL_MODELS = [
  Model('QL-500',   (295, 11811), compression=False, mode_setting=False, expanded_mode=False, cutting=False),
  Model('QL-550',   (295, 11811), compression=False, mode_setting=False),
  Model('QL-560',   (295, 11811), compression=False, mode_setting=False),
  Model('QL-570',   (150, 11811), compression=False, mode_setting=False),
  Model('QL-580N',  (150, 11811)),
  Model('QL-650TD', (295, 11811)),
  Model('QL-700',   (150, 11811), compression=False, mode_setting=False),
  Model('QL-710W',  (150, 11811)),
  Model('QL-720NW', (150, 11811)),
  Model('QL-800',   (150, 11811), two_color=True, compression=False),
  Model('QL-810W',  (150, 11811), two_color=True),
  Model('QL-820NWB',(150, 11811), two_color=True),
  Model('QL-1050',  (295, 35433), number_bytes_per_row=162, additional_offset_r=44),
  Model('QL-1060N', (295, 35433), number_bytes_per_row=162, additional_offset_r=44),
]

class ModelsManager(ElementsManager):
    DEFAULT_ELEMENTS = copy.copy(ALL_MODELS)
    ELEMENTS_NAME = 'model'
