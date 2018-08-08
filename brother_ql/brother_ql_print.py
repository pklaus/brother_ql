#!/usr/bin/env python

"""
Testing the packaged version of the Linux Kernel backend
"""

import argparse, logging, sys

from brother_ql.backends import backend_factory, guess_backend, available_backends
from brother_ql.backends.helpers import discover, send
from brother_ql.output_helpers import log_discovered_devices, textual_description_discovered_devices

logger = logging.getLogger(__name__)

def main():

    # Command line parsing...
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', choices=available_backends, help='Forces the use of a specific backend')
    parser.add_argument('--list-printers', action='store_true', help='List the devices available with the selected --backend')
    parser.add_argument('--debug', action='store_true', help='Enable debugging output')
    parser.add_argument('instruction_file', nargs='?', help='file containing the instructions to be sent to the printer')
    parser.add_argument('printer', metavar='PRINTER_IDENTIFIER', nargs='?', help='Identifier string specifying the printer. If not specified, selects the first detected device.')
    args = parser.parse_args()

    if args.list_printers and not args.backend:
        parser.error('Please specify the backend in order to list available devices.')

    if not args.list_printers and not args.instruction_file:
        parser.error("the following arguments are required: instruction_file")

    # Reading the instruction input file into content variable
    if args.instruction_file == '-':
        try:
            content = sys.stdin.buffer.read()
        except AttributeError:
            content = sys.stdin.read()
    else:
        with open(args.instruction_file, 'rb') as f:
            content = f.read()

    # Setting up the requested level of logging.
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    # State any shortcomings of this software early on.
    if args.backend == 'network':
        logger.warning("The network backend doesn't supply any 'readback' functionality. No status reports will be received.")

    # Select the backend based: Either explicitly stated or derived from identifier. Otherwise: Default.
    selected_backend = None
    if args.backend:
        selected_backend = args.backend
    else:
        try:
            selected_backend = guess_backend(args.printer)
        except:
            logger.info("No backend stated. Selecting the default linux_kernel backend.")
            selected_backend = 'linux_kernel'

    # List any printers found, if explicitly asked to do so or if no identifier has been provided.
    if args.list_printers or not args.printer:
        available_devices = discover(backend_identifier=selected_backend)
        log_discovered_devices(available_devices)

    if args.list_printers:
        print(textual_description_discovered_devices(available_devices))
        sys.exit(0)

    # Determine the identifier. Either selecting the explicitly stated one or using the first found device.
    identifier = None
    if not args.printer:
        "We need to search for available devices and select the first."
        if not available_devices:
            sys.exit("No printer found")
        identifier = available_devices[0]['identifier']
        print("Selecting first device %s" % identifier)
    else:
        "A string identifier for the device was given, let's use it."
        identifier = args.printer

    # Finally, do the actual printing.
    send(instructions=content, printer_identifier=identifier, backend_identifier=selected_backend, blocking=True)

if __name__ == "__main__": main()
