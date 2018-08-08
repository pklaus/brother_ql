import logging

from brother_ql.devicedependent import label_type_specs
from brother_ql.devicedependent import DIE_CUT_LABEL, ENDLESS_LABEL, ROUND_DIE_CUT_LABEL

logger = logging.getLogger(__name__)

def textual_label_description(labels_to_include):
    output = "Supported label sizes:\n"
    output = ""
    fmt = " {label_size:9s} {dots_printable:14s} {label_descr:26s}\n"
    output += fmt.format(label_size="Name", dots_printable="Printable px", label_descr="Description")
    #output += fmt.format(label_size="", dots_printable="width x height", label_descr="")
    for label_size in labels_to_include:
        s = label_type_specs[label_size]
        if s['kind'] in (DIE_CUT_LABEL, ROUND_DIE_CUT_LABEL):
            dp_fmt = "{0:4d} x {1:4d}"
        elif s['kind'] == ENDLESS_LABEL:
            dp_fmt = "{0:4d}"
        else:
            dp_fmt = " - unknown - "
        dots_printable = dp_fmt.format(*s['dots_printable'])
        label_descr = s['name']
        output += fmt.format(label_size=label_size, dots_printable=dots_printable, label_descr=label_descr)
    return output

def log_discovered_devices(available_devices, level=logging.INFO):
    for ad in available_devices:
        result = {'model': 'unknown'}
        result.update(ad)
        logger.log(level, "  Found a label printer: {identifier}  (model: {model})".format(**result))

def textual_description_discovered_devices(available_devices):
    output = ""
    for ad in available_devices:
        output += ad['identifier']
    return output
