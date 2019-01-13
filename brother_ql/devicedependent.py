"""
Deprecated Module brother_ql.devicedependent

This module held constants and settings that were specific to
different QL-series printer models and to different label types.

The content is now split into two modules:

* brother_ql.models
* brother_ql.labels

Please import directly from them as this module will be removed in a future version.
"""

import logging

logger = logging.getLogger(__name__)

logger.warn("deprecation warning: brother_ql.devicedependent is deprecated and will be removed in a future release")

## These module level variables were available here before.
# Concerning labels
DIE_CUT_LABEL = None
ENDLESS_LABEL = None
ROUND_DIE_CUT_LABEL = None
label_type_specs = {}
label_sizes = []
# And concerning printer models
models = []
min_max_length_dots = {}
min_max_feed = {}
number_bytes_per_row = {}
right_margin_addition = {}
modesetting = []
cuttingsupport = []
expandedmode = []
compressionsupport = []
two_color_support = []

## Let's recreate them using the improved data structures
## in brother_ql.models and brother_ql.labels

def _populate_model_legacy_structures():
    from brother_ql.models import ModelsManager
    global models
    global min_max_length_dots, min_max_feed, number_bytes_per_row, right_margin_addition
    global modesetting, cuttingsupport, expandedmode, compressionsupport, two_color_support

    for model in ModelsManager().iter_elements():
        models.append(model.identifier)
        min_max_length_dots[model.identifier] = model.min_max_length_dots
        min_max_feed[model.identifier] = model.min_max_feed
        number_bytes_per_row[model.identifier] = model.number_bytes_per_row
        right_margin_addition[model.identifier] = model.additional_offset_r
        if model.mode_setting: modesetting.append(model.identifier)
        if model.cutting: cuttingsupport.append(model.identifier)
        if model.expanded_mode: expandedmode.append(model.identifier)
        if model.compression: compressionsupport.append(model.identifier)
        if model.two_color: two_color_support.append(model.identifier)

def _populate_label_legacy_structures():
    """
    We contain this code inside a function so that the imports
    we do in here are not visible at the module level.
    """
    global DIE_CUT_LABEL, ENDLESS_LABEL, ROUND_DIE_CUT_LABEL
    global label_sizes, label_type_specs

    from brother_ql.labels import FormFactor
    DIE_CUT_LABEL =       FormFactor.DIE_CUT
    ENDLESS_LABEL =       FormFactor.ENDLESS
    ROUND_DIE_CUT_LABEL = FormFactor.ROUND_DIE_CUT

    from brother_ql.labels import LabelsManager
    lm = LabelsManager()
    label_sizes = list(lm.iter_identifiers())
    for label in lm.iter_elements():
        l = {}
        l['name'] = label.name
        l['kind'] = label.form_factor
        l['color'] = label.color
        l['tape_size'] = label.tape_size
        l['dots_total'] = label.dots_total
        l['dots_printable'] = label.dots_printable
        l['right_margin_dots'] = label.offset_r
        l['feed_margin'] = label.feed_margin
        l['restrict_printers'] = label.restricted_to_models
        label_type_specs[label.identifier] = l

def _populate_all_legacy_structures():
    _populate_label_legacy_structures()
    _populate_model_legacy_structures()

_populate_all_legacy_structures()
