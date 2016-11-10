#!/usr/bin/env python

import argparse

from brother_ql.devicedependent import models, label_sizes, label_type_specs, DIE_CUT_LABEL, ENDLESS_LABEL, ROUND_DIE_CUT_LABEL

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-label-sizes', action='store_true', help='List available label sizes')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    args = parser.parse_args()

    if args.list_models:
        print('Supported models:')
        for model in models: print(" " + model)

    if args.list_label_sizes:
        print('Supported label sizes:')
        for label_size in label_sizes:
            s = label_type_specs[label_size]
            descr = " %-10s " % label_size
            if s['kind'] == DIE_CUT_LABEL: descr += "(%d x %d mm^2)"  % s['tape_size']
            if s['kind'] == ENDLESS_LABEL: descr += "(%d mm endless)" % s['tape_size'][0]
            if s['kind'] == ROUND_DIE_CUT_LABEL: descr += "(%d mm diameter, round)" % s['tape_size'][0]
            print(descr)


if __name__ == "__main__": main()
