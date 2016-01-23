#!/usr/bin/env python3

import os
import sys
import argparse
import json
import itertools

def main(params):
    fastd_to_mac = json.load(params['fastd_file'])
    maclist = params['mac_file'][0].read().splitlines()
    keys = set()
    for k,macs in fastd_to_mac.items():
        for mac in macs:
            if mac in maclist:
                keys.add(k)
    for key in keys:
        print(key)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--fastd-file',
                        help='Fastd socket output file',
                        type=argparse.FileType('r'),
                        default=sys.stdin,
                        nargs=1, metavar='FILE')

    parser.add_argument('-m', '--mac-file',
                        help='Mac-Address file',
                        type=argparse.FileType('r'),
                        nargs=1, metavar='FILE')

    options = vars(parser.parse_args())
    main(options)
