#!/usr/bin/env python

import argparse

from brother_ql.devicedependent import models, label_sizes, label_type_specs, DIE_CUT_LABEL, ENDLESS_LABEL, ROUND_DIE_CUT_LABEL

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='action')
    subparser.add_parser('list-label-sizes', help='List available label sizes')
    subparser.add_parser('list-models',      help='List available models')
    args = parser.parse_args()

    if not args.action:
        parser.error('Please choose an action')

    elif args.action == 'list-models':
        print('Supported models:')
        for model in models: print(" " + model)

    elif args.action == 'list-label-sizes':
        print('Supported label sizes:')
        fmt = " {label_size:9s} {dots_printable:14s} {label_descr:26s}"
        print(fmt.format(label_size="Name", label_descr="Description", dots_printable="Printable px"))
        for label_size in label_sizes:
            s = label_type_specs[label_size]
            if s['kind'] == DIE_CUT_LABEL:
                label_descr = "(%d x %d mm^2)"  % s['tape_size']
                dots_printable = "{0:4d} x {1:4d}".format(*s['dots_printable'])
            if s['kind'] == ENDLESS_LABEL:
                label_descr = "(%d mm endless)" % s['tape_size'][0]
                dots_printable = "{0:4d}".format(*s['dots_printable'])
            if s['kind'] == ROUND_DIE_CUT_LABEL:
                label_descr = "(%d mm diameter, round)" % s['tape_size'][0]
                dots_printable = "{0:4d} x {1:4d}".format(*s['dots_printable'])
            print(fmt.format(label_size=label_size, label_descr=label_descr, dots_printable=dots_printable))

if __name__ == "__main__": main()
