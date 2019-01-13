
from attr import attrs, attrib
from typing import List, Tuple
from enum import Enum

import copy

from brother_ql.helpers import ElementsManager

class FormFactor(Enum):
    """
    Enumeration representing the form factor of a label.
    The labels for the Brother QL series are supplied either as die-cut (pre-sized), or for more flexibility the
    continuous label tapes offer the ability to vary the label length.
    """
    #: rectangular die-cut labels
    DIE_CUT = 1
    #: endless (continouse) labels
    ENDLESS = 2
    #: round die-cut labels
    ROUND_DIE_CUT = 3

class Color(Enum):
    """
    Enumeration representing the colors to be printed on a label. Most labels only support printing black on white.
    Some newer ones can also print in black and red on white.
    """
    #: The label can be printed in black & white.
    BLACK_WHITE = 0
    #: The label can be printed in black, white & red.
    BLACK_RED_WHITE = 1

@attrs
class Label(object):
    """
    This class represents a label. All specifics of a certain label
    and what the rasterizer needs to take care of depending on the
    label choosen, should be contained in this class.
    """
    #: A string identifier given to each label that can be selected. Eg. '29'.
    identifier = attrib(type=str)
    #: The tape size of a single label (width, lenght) in mm. For endless labels, the length is 0 by definition.
    tape_size = attrib(type=Tuple[int, int])
    #: The type of label
    form_factor = attrib(type=FormFactor)
    #: The total area (width, length) of the label in dots (@300dpi).
    dots_total = attrib(type=Tuple[int, int])
    #: The printable area (width, length) of the label in dots (@300dpi).
    dots_printable = attrib(type=Tuple[int, int])
    #: The required offset from the right side of the label in dots to obtain a centered printout.
    offset_r = attrib(type=int)
    #: An additional amount of feeding when printing the label.
    #: This is non-zero for some smaller label sizes and for endless labels.
    feed_margin = attrib(type=int, default=0)
    #: If a label can only be printed with certain label printers, this member variable lists the allowed ones.
    #: Otherwise it's an empty list.
    restricted_to_models = attrib(type=List[str], factory=list)
    #: Some labels allow printing in red, most don't.
    color = attrib(type=Color, default=Color.BLACK_WHITE)

    def works_with_model(self, model): # type: bool
        """
        Method to determine if certain label can be printed by the specified printer model.
        """
        if self.restricted_to_models and model not in models: return False
        else: return True

    @property
    def name(self): # type: str
        out = ""
        if 'x' in self.identifier:
            out = '{0}mm x {1}mm die-cut'.format(*self.tape_size)
        elif self.identifier.startswith('d'):
            out = '{0}mm round die-cut'.format(self.tape_size[0])
        else:
            out = '{0}mm endless'.format(self.tape_size[0])
        if self.color == Color.BLACK_RED_WHITE:
            out += ' (black/red/white)'
        return out

ALL_LABELS = (
  Label("12",     ( 12,   0), FormFactor.ENDLESS,       ( 142,    0), ( 106,    0),  29 , feed_margin=35),
  Label("29",     ( 29,   0), FormFactor.ENDLESS,       ( 342,    0), ( 306,    0),   6 , feed_margin=35),
  Label("38",     ( 38,   0), FormFactor.ENDLESS,       ( 449,    0), ( 413,    0),  12 , feed_margin=35),
  Label("50",     ( 50,   0), FormFactor.ENDLESS,       ( 590,    0), ( 554,    0),  12 , feed_margin=35),
  Label("54",     ( 54,   0), FormFactor.ENDLESS,       ( 636,    0), ( 590,    0),   0 , feed_margin=35),
  Label("62",     ( 62,   0), FormFactor.ENDLESS,       ( 732,    0), ( 696,    0),  12 , feed_margin=35),
  Label("62red",  ( 62,   0), FormFactor.ENDLESS,       ( 732,    0), ( 696,    0),  12 , feed_margin=35, color=Color.BLACK_RED_WHITE),
  Label("102",    (102,   0), FormFactor.ENDLESS,       (1200,    0), (1164,    0),  12 , feed_margin=35, restricted_to_models=['QL-1050', 'QL-1060N']),
  Label("17x54",  ( 17,  54), FormFactor.DIE_CUT,       ( 201,  636), ( 165,  566),   0 ),
  Label("17x87",  ( 17,  87), FormFactor.DIE_CUT,       ( 201, 1026), ( 165,  956),   0 ),
  Label("23x23",  ( 23,  23), FormFactor.DIE_CUT,       ( 272,  272), ( 202,  202),  42 ),
  Label("29x42",  ( 29,  42), FormFactor.DIE_CUT,       ( 342,  495), ( 306,  425),   6 ),
  Label("29x90",  ( 29,  90), FormFactor.DIE_CUT,       ( 342, 1061), ( 306,  991),   6 ),
  Label("39x90",  ( 38,  90), FormFactor.DIE_CUT,       ( 449, 1061), ( 413,  991),  12 ),
  Label("39x48",  ( 39,  48), FormFactor.DIE_CUT,       ( 461,  565), ( 425,  495),   6 ),
  Label("52x29",  ( 52,  29), FormFactor.DIE_CUT,       ( 614,  341), ( 578,  271),   0 ),
  Label("62x29",  ( 62,  29), FormFactor.DIE_CUT,       ( 732,  341), ( 696,  271),  12 ),
  Label("62x100", ( 62, 100), FormFactor.DIE_CUT,       ( 732, 1179), ( 696, 1109),  12 ),
  Label("102x51", (102,  51), FormFactor.DIE_CUT,       (1200,  596), (1164,  526),  12 , restricted_to_models=['QL-1050', 'QL-1060N']),
  Label("102x152",(102, 153), FormFactor.DIE_CUT,       (1200, 1804), (1164, 1660),  12 , restricted_to_models=['QL-1050', 'QL-1060N']),
  Label("d12",    ( 12,  12), FormFactor.ROUND_DIE_CUT, ( 142,  142), (  94,   94), 113 , feed_margin=35),
  Label("d24",    ( 24,  24), FormFactor.ROUND_DIE_CUT, ( 284,  284), ( 236,  236),  42 ),
  Label("d58",    ( 58,  58), FormFactor.ROUND_DIE_CUT, ( 688,  688), ( 618,  618),  51 ),
)

class LabelsManager(ElementsManager):
    DEFAULT_ELEMENTS = copy.copy(ALL_LABELS)
    ELEMENT_NAME = "label"
