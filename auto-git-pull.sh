#!/bin/bash

set -e

GITBASEDIR=/etc/fastd/.peers/fastd-peers-clients

SIGHUP_PIDFILES=$(for s in $(seq -w 02 07); do echo "/var/run/fastd.$s-clients.pid"; done)
SIGUSR2_PIDFILES="/var/run/fastd.01-clients-v4.pid /var/run/fastd.01-clients-v6.pid"

function reload() {
	echo reloading with HUP
	for f in $SIGHUP_PIDFILES; do 
		echo $f;
		pkill -HUP -F "$f"
	done
	echo reloading with USR2
	for f in $SIGUSR2_PIDFILES; do
		echo $f;
		pkill -USR2 -F "$f"
	done
}

cd $GITBASEDIR

[ -d .git ] || ( echo "bad repo basedir"; exit 1 )

if [ ! -z "$(git status --porcelain)" ]; then
	echo "git is not clean"
	exit 1
fi

while true; do
	old_commit=$(git rev-parse HEAD)
	git pull || echo git failed # ignore error code - no reason to terminate script
	new_commit=$(git rev-parse HEAD)
	if [ "$old_commit" != "$new_commit" ]; then
		reload
	fi
	sleep 60
done

