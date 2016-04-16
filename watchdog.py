#!/usr/bin/env python3

# detect segment shortcuts and propose resolutions

import argparse
import json
import time
import parser.fastd
import parser.batman
import requests

def main(params):
    config = json.load(params['config_file'])
    nodename = params['node_name']

    watchdog = Watchdog(config, nodename)

    while True:
        for segment in config['segments']:
            watchdog.check_segment(segment)
        time.sleep(10)

class Watchdog:
    def __init__(self, config, nodename):
        self.config = config
        self.nodename = nodename
        self.nodeconfig = config['nodes'][nodename]
        self.fastd_parser = parser.fastd.FastdParser(self.nodeconfig['fastd_path'])
        self.batman_parser = parser.batman.BatmanParser("/sys/kernel/debug/batman_adv")
        self.known_shorts = {}
        webhook_file = self.config.get("slack-webhook-url-file")
        self.webhook_url = None
        if webhook_file != None:
            with open(webhook_file, 'r') as f:
                self.webhook_url = f.read().strip()
            print("Sending alerts to slack!")

    def check_segment(self, segment):
        #print("Checking segment {} on supernode {}".format(segment, self.nodename))
        segment_config = self.config['segments'][segment]
        batman_if = segment_config['batman']

        gws = self.batman_parser.gateways(batman_if)

        for gw in gws:
            interface_config = self.config['interfaces'][gw.interface]
            if not interface_config['ignore']:
                if gw.gateway in segment_config['gateways']:
                    print("matching gw: {}".format(gw))
                else:
                    print("bad gw: {}".format(gw))
                    other_seg = self.find_segment_of_gateway(gw.gateway)
                    msg = ""
                    if other_seg:
                        msg += ("shortcut {} <-> {} detected\n".format(segment, other_seg))
                    else:
                        msg += ("link from segment {} to unknown gateway {} detected\n".format(segment, gw.gateway))
                    try:
                        socketname = interface_config['fastd_socket']
                        fastd_status = self.fastd_parser.status(socketname)
                        peer = self.fastd_parser.peer_for_mac(fastd_status, gw.nexthop)[0]
                        if peer:
                            msg += ("peer is {} (IP: {}, MACs: {})\n".format(peer[1]['name'], peer[1]['address'], peer[1]['connection']['mac_addresses']))
                            msg += ('key "{}";\n'.format(peer[0]))
                            known = self.known_shorts.get(peer[0])
                            if self.webhook_url != None and known == None or known.get('segment') != segment:
                                print("New entry - send alert!") # TODO implement alert
                                self.known_shorts[peer[0]] = { 'segment': segment }
                                payload= { 'username': 'watchdog on '+self.nodename, 'text': "```" + msg + "```", 'icon_emoji': ':dog2' }
                                r=requests.post(self.webhook_url,data=json.dumps(payload))
                                print("{} {}".format(r.status_code, r.text))

                    except Exception as e:
                        print("error finding fastd key: {}".format(e))

                    print(msg)

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

