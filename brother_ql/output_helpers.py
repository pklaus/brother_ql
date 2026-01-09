import logging

from brother_ql.labels import LabelsManager, FormFactor

logger = logging.getLogger(__name__)

def textual_label_description(labels_to_include):
    output = "Supported label sizes:\n"
    output = ""
    fmt = " {label_size:9s} {dots_printable:14s} {label_descr:26s}\n"
    output += fmt.format(label_size="Name", dots_printable="Printable px", label_descr="Description")
    #output += fmt.format(label_size="", dots_printable="width x height", label_descr="")
    labels_manager = LabelsManager()
    for label_size in labels_to_include:
        label = labels_manager.get_label_by_identifier(label_size)
        if label.form_factor in (FormFactor.DIE_CUT, FormFactor.ROUND_DIE_CUT):
            dp_fmt = "{0:4d} x {1:4d}"
        elif label.form_factor in (FormFactor.ENDLESS, FormFactor.PTOUCH_ENDLESS):
            dp_fmt = "{0:4d}"
        else:
            dp_fmt = " - unknown - "
        dots_printable = dp_fmt.format(*label.dots_printable)
        label_descr = label.name
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
