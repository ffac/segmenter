#!/bin/bash

# usage e.g.:
#   sh to_fastd_keys.sh  -m ./segments/ffac_segment02_wgs84.shp.mac.txt <../supernode-03-v4-sock.json

jq '.peers|to_entries|map({key:.key,value:.value.connection.mac_addresses})|from_entries' |
	./to_fastd_keys.py "$@"
