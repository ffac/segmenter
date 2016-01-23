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
        "basename": "unknown",
        "nodes": {}
    }

    links = {}
    nodes = {}

    for file in params['graph_file']:
        with open(file, 'r') as file_handle:
            graphdb = json.load(file_handle)
            for key, link in enumerate(graphdb["batadv"]["links"]):
                if (link["vpn"] == False):
                    source = graphdb["batadv"]["nodes"][link["source"]]
                    target = graphdb["batadv"]["nodes"][link["target"]]
                    if "node_id" in source and "node_id" in target:
                        links[source["node_id"]] = target["node_id"]

    for file in params['shape_file']:
        sf = shapefile.Reader(file)
        for shape in sf.shapes():
            bn = os.path.basename(file)
            segments.append({
              "polygon": asShape(shape),
              "basename" : bn,
              "nodes": {}
            })

    for file in params['nodes_file']:
        with open(file, 'r') as file_handle:
            nodedb = json.load(file_handle)
            for id,n in nodedb["nodes"].items():
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
    collector = []
    for id,n in unknown["nodes"].items():
        if (id in links):
            target = links[id]
            if (target in nodes):
                if ("segment" in nodes[target]):
                    nodes[target]["segment"]["nodes"][id] = n
                    collector.append(id)
    for id in collector:
        del unknown["nodes"][id]

    segments.append(unknown);

    for segment in segments:
        print("Name: " + segment["basename"])
        for id, n in segment["nodes"].items():
            hostname = ""
            if "nodeinfo" in n and "hostname" in n["nodeinfo"]:
                hostname = n["nodeinfo"]["hostname"]
            print("  " + id + " ("+hostname+")")
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

    options = vars(parser.parse_args())
    main(options)
