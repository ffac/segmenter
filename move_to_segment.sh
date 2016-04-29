#!/bin/bash

set -e

REPO=$1
SEGMENT=$2
KEY=$3
NAME=$4

if [ -z "$SUPERNODE" ]; then
	SUPERNODE=$HOSTNAME
fi

case "$SEGMENT" in
	[0-9][0-9])
		;;
	[0-9])
		SEGMENT=0$SEGMENT
		;;
	*)
		echo "Bad segment $SEGMENT"
		exit 1
esac

key_regex='^[0-9a-f]{64}$'

if [[ ! "$KEY" =~ $key_regex ]]; then
	echo "bad key $KEY"
	exit 1
fi

if [ -z "$NAME" ]; then
	NAME="key-$KEY"
fi

name_regex='^[-0-9a-zA-Z_.]{12,128}$'

if [[ ! "$NAME" =~ $name_regex ]]; then
	echo "bad filename $NAME"
	exit 1
fi

echo "moving node $NAME with key $KEY to segment $SEGMENT"

cd "$REPO"

[ -d .git ] || ( echo "bad repo basedir"; exit 1 )

[ -d segment-$SEGMENT ] || ( echo "segment dir does not exist"; exit 1 )

if [ ! -z "$(git status --porcelain)" ]; then
	echo "git is not clean"
	exit 1
fi

git pull


old_commit=$(git rev-parse HEAD)

trap "git reset --hard \"$old_commit\"" EXIT

old_entry=$(git grep -l '^key "'$KEY'";' || true)

if [ "$old_entry" != "" ]; then
	if [ ! -f "$old_entry" ]; then
		echo "existing entry is not a (single) file!"
		exit 1
	fi
	git rm "$old_entry"
fi

FULLNAME="segment-$SEGMENT/$NAME"

if [ -e "$FULLNAME" ]; then
	echo "file already exists: $FULLNAME"
	git reset --hard
	exit 1
fi

echo "# Autosegmenter at $SUPERNODE" >"$FULLNAME"
echo "key \"$KEY\";" >"$FULLNAME"

git add "$FULLNAME"

if [ ! -z "$(git status --porcelain)" ]; then
	export GIT_AUTHOR_NAME="Autosegmenter"
	export GIT_AUTHOR_EMAIL="autosegmenter@gondor.com"
	export GIT_COMMITTER_NAME="Autosegmenter"
	export GIT_COMMITTER_EMAIL="autosegmenter@gondor.com"
	git commit -m "autosegmenter at $SUPERNODE added $KEY to segment $SEGMENT"

	git push
else
	echo "No changes to commit"
fi

trap - EXIT

