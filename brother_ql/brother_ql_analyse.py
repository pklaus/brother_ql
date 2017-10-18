#!/usr/bin/env python

import sys, argparse, logging

from brother_ql.reader import BrotherQLReader

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The file to analyze', type=argparse.FileType('rb'))
    parser.add_argument('--loglevel', type=lambda x: getattr(logging, x), default=logging.WARNING, help='The loglevel to apply')
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, format='%(levelname)s: %(message)s', level=args.loglevel)

    try:
        args.file = args.file.buffer
    except AttributeError:
        pass

    br = BrotherQLReader(args.file)
    br.analyse()

if __name__ == '__main__':
    main()
