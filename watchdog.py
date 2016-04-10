#!/usr/bin/env python3

# detect segment shortcuts and propose resolutions

import argparse
import json
import time
import parser.fastd
import parser.batman

def main(params):
    config = json.load(params['config_file'])
    nodename = params['node_name']

    watchdog = Watchdog(config, nodename)

    for segment in config['segments']:
        watchdog.check_segment(segment)

class Watchdog:
    def __init__(self, config, nodename):
        self.config = config
        self.nodename = nodename
        self.nodeconfig = config['nodes'][nodename]
        self.fastd_parser = parser.fastd.FastdParser(self.nodeconfig['fastd_path'])
        self.batman_parser = parser.batman.BatmanParser("/sys/kernel/debug/batman_adv")

    def check_segment(self, segment):
        print("Checking segment {} on supernode {}".format(segment, self.nodename))
        segment_config = self.config['segments'][segment]
        batman_if = segment_config['batman']

        gws = self.batman_parser.gateways(batman_if)

        for gw in gws:
            if gw.gateway in segment_config['gateways']:
                print("matching gw: {}".format(gw))
            else:
                print("bad gw: {}".format(gw))
                other_seg = self.find_segment_of_gateway(gw.gateway)
                if other_seg:
                    print("shortcut {} <-> {} detected".format(segment, other_seg))
                else:
                    print("link from segment {} to unknown gateway {} detected".format(segment, gw.gateway))
                try:
                    socketname = self.config['fastd-sockets'][gw.interface]
                    fastd_status = self.fastd_parser.status(socketname)
                    peer = self.fastd_parser.peer_for_mac(fastd_status, gw.nexthop)[0]
                    if peer:
                        print("peer is {} (IP: {}, MACs: {})".format(peer[1]['name'], peer[1]['address'], peer[1]['connection']['mac_addresses']))
                        print('key "{}";'.format(peer[0]))
                except Exception as e:
                    print("error finding fastd key: {}".format(e))

        print("\n")

    def find_segment_of_gateway(self, gw):
        for seg in self.config['segments']:
            if gw in self.config['segments'][seg]['gateways']:
                return seg
        return None

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('-c', '--config-file',
                        help='Watchdog config file',
                        type=argparse.FileType('r'),
                        metavar='FILE')

    argparser.add_argument('-n', '--node-name',
                        help='name of current supernode')

    options = vars(argparser.parse_args())
    main(options)

