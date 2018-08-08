#!/usr/bin/env python

"""
Helpers for the subpackage brother_ql.backends

* device discovery
* printing
"""

import logging, time

from brother_ql.backends import backend_factory, guess_backend
from brother_ql.reader import interpret_response

logger = logging.getLogger(__name__)

def discover(backend_identifier='linux_kernel'):

    be = backend_factory(backend_identifier)
    list_available_devices = be['list_available_devices']
    BrotherQLBackend       = be['backend_class']

    available_devices = list_available_devices()
    return available_devices

def send(instructions, printer_identifier=None, backend_identifier=None, blocking=True):
    """
    Send instruction bytes to a printer.

    :param bytes instructions: The instructions to be sent to the printer.
    :param str printer_identifier: Identifier for the printer.
    :param str backend_identifier: Can enforce the use of a specific backend.
    :param bool blocking: Indicates whether the function call should block while waiting for the completion of the printing.
    """

    selected_backend = None
    if backend_identifier:
        selected_backend = backend_identifier
    else:
        try:
            selected_backend = guess_backend(printer_identifier)
        except:
            logger.info("No backend stated. Selecting the default linux_kernel backend.")
            selected_backend = 'linux_kernel'

    be = backend_factory(selected_backend)
    list_available_devices = be['list_available_devices']
    BrotherQLBackend       = be['backend_class']

    printer = BrotherQLBackend(printer_identifier)

    start = time.time()
    logger.info('Sending instructions to the printer. Total: %d bytes.', len(instructions))
    printer.write(instructions)
    if not blocking:
        return
    if selected_backend == 'network':
        """ No need to wait for completion. The network backend doesn't support readback. """
        return
    printing_completed = False
    waiting_to_receive = False
    while time.time() - start < 10:
        data = printer.read()
        if not data:
            time.sleep(0.005)
            continue
        try:
            result = interpret_response(data)
        except ValueError:
            logger.error("TIME %.3f - Couln't understand response: %s", time.time()-start, data)
            continue
        logger.debug('TIME %.3f - result: %s', time.time()-start, result)
        if result['errors']:
            logger.error('Errors occured: %s', result['errors'])
        if result['status_type'] == 'Printing completed':
            printing_completed = True
        if result['status_type'] == 'Phase change' and result['phase_type'] == 'Waiting to receive':
            waiting_to_receive = True
        if printing_completed and waiting_to_receive:
            break
    if not printing_completed:
        logger.warning("'printing completed' status not received.")
    if not waiting_to_receive:
        logger.warning("'waiting to receive' status not received.")
    if (not printing_completed) or (not waiting_to_receive):
        logger.warning('Printing potentially not successful?')
    if printing_completed and waiting_to_receive:
        logger.info("Printing was successful. Waiting for the next job.")
