#!/usr/bin/env python

"""
Printer device discovery using the different brother_ql.backends
"""

import logging

from brother_ql.backends import backend_factory, guess_backend, available_backends

logger = logging.getLogger(__name__)

def discover(backend_name='linux_kernel'):

    be = backend_factory(selected_backend)
    list_available_devices = be['list_available_devices']
    BrotherQLBackend       = be['backend_class']

    available_devices = list_available_devices()
    return available_devices

def pretty_print_discovered_devices(available_devices):
    for ad in available_devices:
        result = {'model': 'unknown'}
        result.update(ad)
        logger.info("  Found a label printer: {identifier}  (model: {model})".format(**result))

        for printer in available_devices:
            print(printer['identifier'])
        sys.exit(0)
