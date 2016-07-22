#!/usr/bin/env python

import sys, argparse, logging, struct, io, logging, sys, os, time
from pprint import pprint, pformat

from brother_ql.reader import OPCODES, chunker, merge_specific_instructions, interpret_response, match_opcode, hex_format
from brother_ql.backends import backend_factory, guess_backend

logger = logging.getLogger(__name__)

class BrotherQL_USBdebug(object):

    def __init__(self, dev, instructions_data, backend='linux_kernel'):

        be_cls = backend_factory(backend)['backend_class']
        self.be = be_cls(dev)

        self.sleep_time = 0.0
        self.sleep_before_read = 0.0
        self.continue_reading_for = 3.0
        self.start = time.time()
        self.interactive = False
        self.merge_specific_instructions = True
        if type(instructions_data) in (str,):
            with open(instructions_data, 'rb') as f:
                self.instructions_data = f.read()
        elif type(instructions_data) in (bytes,):
            self.instructions_data = instructions_data
        else:
            raise NotImplementedError('Only filename or bytes supported for instructions_data argument')
        response = self.be.read()
        if response:
            logger.warning('Received response before sending instructions: {}'.format(hex_format(response)))

    def continue_reading(self, seconds=3.0):
        start = time.time()
        while time.time() - start < seconds:
            data = self.be.read()
            if data != b'':
                global_time = time.time() - self.start
                print('TIME %.2f' % global_time)
                self.log_interp_response(data)
            time.sleep(0.001)

    def log_interp_response(self, data):
        try:
            interp_result = interpret_response(data)
            logger.info("Interpretation of the response: '{status_type}' (phase: {phase_type}), '{media_type}' {media_width}x{media_length} mm^2, errors: {errors}".format(**interp_result))
        except:
            logger.error("Couln't interpret response: %s", hex_format(data))

    def print_and_debug(self):

        self.continue_reading(0.2)

        instructions = chunker(self.instructions_data)
        instructions = merge_specific_instructions(instructions, join_preamble=True, join_raster=self.merge_specific_instructions)
        for instruction in instructions:
            opcode = match_opcode(instruction)
            opcode_def = OPCODES[opcode]
            cmd_name = opcode_def[0]
            hex_instruction = hex_format(instruction).split()
            if len(hex_instruction) > 100:
                hex_instruction = ' '.join(hex_instruction[0:70] + ['[...]'] + hex_instruction[-30:])
            else:
                hex_instruction = ' '.join(hex_instruction)
            logger.info("CMD {} FOUND. Instruction: {} ".format(cmd_name, hex_instruction))
            if self.interactive: input('Continue?')
            # WRITE
            self.be.write(instruction)
            # SLEEP BEFORE READ
            time.sleep(self.sleep_before_read)
            # READ
            response = self.be.read()
            #response += self.be.read()
            if response != b'':
                logger.info("Response from the device: {}".format(hex_format(response)))
                self.log_interp_response(response)
            # SLEEP BETWEEN INSTRUCTIONS
            time.sleep(self.sleep_time)

        self.continue_reading(self.continue_reading_for)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The file to analyze')
    parser.add_argument('dev', help='The device to use. Can be usb://0x04f9:0x2015 or /dev/usb/lp0 for example')
    parser.add_argument('--sleep-time', type=float, help='time in seconds to sleep between instructions')
    parser.add_argument('--sleep-before-read', type=float, help='time in seconds to sleep before reading response')
    parser.add_argument('--continue-reading-for', type=float, help='continue reading after sending the last commands (time in seconds)')
    parser.add_argument('--interactive', action='store_true', help='interactive mode')
    parser.add_argument('--split-raster', action='store_true', help='even split preamble and raster instructions into single write operations')
    parser.add_argument('--debug', action='store_true', help='enable debug mode')
    args = parser.parse_args()

    # SETUP
    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=loglevel, format='%(levelname)s: %(message)s')

    try:
        backend = guess_backend(args.dev)
    except ValueError as e:
        parser.error(e.msg)

    br = BrotherQL_USBdebug(args.dev, args.file, backend=backend)
    if args.interactive: br.interactive = True
    if args.sleep_time: br.sleep_time = args.sleep_time
    if args.sleep_before_read: br.sleep_before_read = args.sleep_before_read
    if args.split_raster: br.merge_specific_instructions = False
    if args.continue_reading_for: br.continue_reading_for = args.continue_reading_for

    # GO
    br.print_and_debug()


if __name__ == '__main__':
    main()
