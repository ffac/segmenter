DATE=$(date +"%Y%m%d-%H%M")
for sn in `seq -w 01 06`; do ssh root@$sn.nodes.freifunk-aachen.de 'for a in /tmp/fastd-*client*.sock; do nc -U "$a"; done'; done | jq -s 'map(.peers)|map(with_entries(select(.value.connection.mac_addresses|length > 0)|{key : .value.connection.mac_addresses[],value : .key}))|add' >data/keys-$DATE.json

curl http://data.aachen.freifunk.net/nodes.json >data/nodes-$DATE.json
curl http://data.aachen.freifunk.net/graph.json >data/graph-$DATE.json

./segmenter.py -d segments -a aliases/supernodes.json -n data/nodes-$DATE.json -g data/graph-$DATE.json -s shapefiles/ffac_segment*.shp  -k data/keys-$DATE.json

