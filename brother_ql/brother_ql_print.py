#!/usr/bin/env python

"""
Testing the packaged version of the Linux Kernel backend
"""

import argparse, logging, sys, time
from pprint import pprint

from brother_ql.backends import backend_factory, guess_backend, available_backends
from brother_ql.reader import interpret_response

logger = logging.getLogger(__name__)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=available_backends, help='Forces the use of a specific backend')
    parser.add_argument('--list-printers', action='store_true', help='List the devices available with the selected --backend')
    parser.add_argument('--debug', action='store_true', help='Enable debugging output')
    parser.add_argument('instruction_file', nargs='?', help='file containing the instructions to be sent to the printer')
    parser.add_argument('device', metavar='DEVICE_STRING_DESCRIPTOR', nargs='?', help='String descriptor for specific device. If not specified, select first detected device')
    args = parser.parse_args()

    if args.list_printers and not args.backend:
        parser.error('Please specify the backend in order to list available devices.')

    if not args.list_printers and not args.instruction_file:
        parser.error("the following arguments are required: instruction_file")

    if args.instruction_file == '-':
        try:
            content = sys.stdin.buffer.read()
        except AttributeError:
            content = sys.stdin.read()
    else:
        with open(args.instruction_file, 'rb') as f:
            content = f.read()

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level)
    if args.backend == 'network':
        logger.warning("The network backend doesn't supply any 'readback' functionality. No status reports will be received.")

    selected_backend = None
    if args.backend:
        selected_backend = args.backend
    else:
        try:
            selected_backend = guess_backend(args.device)
        except:
            logger.info("No backend stated. Selecting the default linux_kernel backend.")
            selected_backend = 'linux_kernel'

    be = backend_factory(selected_backend)
    list_available_devices = be['list_available_devices']
    BrotherQLBackend       = be['backend_class']

    if args.list_printers:
        for printer in list_available_devices():
            print(printer['string_descr'])
            sys.exit(0)

    string_descr = None
    if not args.device:
        "We need to search for available devices and select the first."
        ad = list_available_devices()
        if not ad:
            sys.exit("No printer found")
        string_descr = ad[0]['string_descr']
        print("Selecting first device %s" % string_descr)
    else:
        "A string descriptor for the device was given, let's use it."
        string_descr = args.device

    printer = BrotherQLBackend(string_descr)

    start = time.time()
    logger.info('Sending instructions to the printer. Total: %d bytes.', len(content))
    printer.write(content)
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
        if result['status_type'] == 'Printing completed': printing_completed = True
        if result['status_type'] == 'Phase change' and result['phase_type'] == 'Waiting to receive': waiting_to_receive = True
        if printing_completed and waiting_to_receive:
            break
    if not (printing_completed and waiting_to_receive):
        logger.warning('Printing potentially not successful?')

if __name__ == "__main__": main()
