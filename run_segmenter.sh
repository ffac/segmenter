DATE=$(date +"%Y%m%d-%H%M")
for sn in `seq -w 01 06`; do ssh root@$sn.nodes.freifunk-aachen.de 'for a in /tmp/fastd-*client*.sock; do nc -U "$a"; done'; done | jq -s 'map(.peers)|map(with_entries(select(.value.connection.mac_addresses|length > 0)|{key : .value.connection.mac_addresses[],value : .key}))|add' >data/keys-$DATE.json

#curl http://www.freifunk-aachen.de/map/data/nodes.json >data/nodes-$DATE.json
curl http://data.aachen.freifunk.net/nodes.json >data/nodes_2-$DATE.json
jq '. + {nodes: (.nodes | map({key: .nodeinfo.node_id, value:.})| from_entries)}' data/nodes_2-$DATE.json >data/nodes-$DATE.json
#curl http://www.freifunk-aachen.de/map/data/graph.json >data/graph-$DATE.json
curl http://data.aachen.freifunk.net/graph.json >data/graph-$DATE.json

./segmenter.py -d segments -a aliases/supernodes.json -n data/nodes-$DATE.json -g data/graph-$DATE.json -s shapefiles/ffac_segment*.shp  -k data/keys-$DATE.json

