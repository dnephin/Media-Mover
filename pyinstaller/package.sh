#!/bin/bash

if [ -z $1 ]; then
	echo "No version number."
	exit -1
fi

echo "Packing version $1"
cd ..
tar -cz --exclude=.git* --exclude=dist --exclude=build -f MediaMover-source-$1.tar.gz MediaMover/
tar -czf MediaMover-linux-binary-$1.tar.gz MediaMover/dist/
