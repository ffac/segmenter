#!/usr/bin/env python3

import os
import argparse
import shapefile
from shapely.geometry import Point, shape, asShape
import json
import pprint

def main(params):
    os.makedirs(params['dest_dir'], exist_ok=True)

    segments = []

    unknown = {
        "id": "u",
        "nodes": {}
    }

    links = {}
    nodes = {}

    aliases = {}

    mac_to_fastd = json.load(params['key_file'])

    for file in params['alias_file']:
        with open(file, 'r') as file_handle:
            aliasdb = json.load(file_handle)
            for alias in aliasdb:
                aliases[alias["node_id"]] = alias


    for file in params['graph_file']:
        with open(file, 'r') as file_handle:
            graphdb = json.load(file_handle)
            for key, link in enumerate(graphdb["batadv"]["links"]):
                source = graphdb["batadv"]["nodes"][link["source"]]
                if ("node_id" in source):
                    source = source["node_id"]
                else:
                    source = source["id"].replace(":", "")

                target = graphdb["batadv"]["nodes"][link["target"]]
                if ("node_id" in target):
                    target = target["node_id"]
                else:
                    target = target["id"].replace(":", "")

                if not source in links:
                    links[source] = target
                if not target in links:
                    links[target] = source


    for file in params['shape_file']:
        with open(file, 'r') as file_handle:
            shapedefs = json.load(file_handle)
            for shapedef in shapedefs:
                sf = shapefile.Reader(shapedef["file"])
                for shape in sf.shapes():
                    segments.append({
                        "polygon": asShape(shape),
                        "id": shapedef["id"],
                        "nodes": {}
                    })

    for file in params['nodes_file']:
        with open(file, 'r') as file_handle:
            nodedb = json.load(file_handle)
            for n in nodedb["nodes"]:
                id=n["nodeinfo"]["node_id"]
                if not id in aliases:
                    if not "flags" in n or not "gateway" in n["flags"] or n["flags"]["gateway"] == False:
                        if ("nodeinfo" in n) \
                                and ("location" in n["nodeinfo"])\
                                and ("longitude" in n["nodeinfo"]["location"])\
                                and ("latitude" in n["nodeinfo"]["location"]):

                            point = Point(n["nodeinfo"]["location"]["longitude"], n["nodeinfo"]["location"]["latitude"])
                            contained = False
                            for segment in segments:
                                if (segment["polygon"].contains(point)):
                                    n["segment"] = segment
                                    segment["nodes"][id] = n
                                    contained = True
                                    break
                            if not contained:
                                unknown["nodes"][id] = n
                        else:
                            unknown["nodes"][id] = n
                        nodes[id] = n


    # Check for links of unknown nodes to nodes in other segments
    def follow_links():
        done = False
        while not done:
            done = True
            collector = []
            for id,n in unknown["nodes"].items():
                if (id in links):
                    target = links[id]
                    if (target in nodes):
                        if ("segment" in nodes[target]):
                            n["segment"] = nodes[target]["segment"]
                            nodes[target]["segment"]["nodes"][id] = n
                            collector.append(id)
                            done = False
            for id in collector:
                del unknown["nodes"][id]

    follow_links()

    segments.append(unknown);

    # Write mac addresses to destination dir
    dest = params["dest_dir"]
    for segment in segments:
        segment_dir = dest+"/segment_"+segment["id"]
        os.makedirs(segment_dir, exist_ok=True)
        with open(dest+"/segment_"+segment["id"]+".mac.txt", "w") as f:
            print("Name: " + segment["id"])
            for id, n in segment["nodes"].items():
                hostname = ""
                if "nodeinfo" in n and "hostname" in n["nodeinfo"]:
                    hostname = n["nodeinfo"]["hostname"]
                print("  " + id + " ("+hostname+")")
                try:
                    tun_mac = n["nodeinfo"]["network"]["mesh"]["bat0"]["interfaces"]["tunnel"][0]
                    f.write(tun_mac+"\n")
                    try:
                        fastd_key = mac_to_fastd[tun_mac]
                        with open(segment_dir+"/"+ id  + "-" + hostname, "w") as nf:
                            nf.write("key \"" + fastd_key + "\";\n")
                    except KeyError:
                        print("Node without fastd key!")
                except KeyError:
                    print("Node without tunnel!")
        print("")




if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--dest-dir', action='store',
                        help='Write output to destination directory',
                        required=True)

    parser.add_argument('-s', '--shape-file',
                        help='Segment polygon',
                        nargs='+', default=[], metavar='FILE')

    parser.add_argument('-g', '--graph-file',
                        help='Graph file',
                        nargs='+', default=[], metavar='FILE')

    parser.add_argument('-n', '--nodes-file',
                        help='Nodes file',
                        nargs='+', default=[], metavar='FILE')

    parser.add_argument('-a', '--alias-file',
                        help='Alias file',
                        nargs='+', default=[], metavar='FILE')

    parser.add_argument('-k', '--key-file',
                        help='Key file',
                        type=argparse.FileType('r'),
                        metavar='FILE')


    options = vars(parser.parse_args())
    main(options)
