#!/bin/bash
###############################################################################
# unmount_workspace.sh : Unmounts all the various --bind mounts inside
###############################################################################

set -e

target=$1

if [ -z "$target" ]; then
    echo "USAGE: $0 TARGET_DIR"
    exit -1
fi

if [ ! -e $target ]; then
    echo "$target does not exist!"
    exit -1
fi

if [ `whoami` != "root" ]; then
    echo "You have to be root to unmount a workspace!"
    exit -1
fi

TMP=`mount|grep $target|awk '{print $3}'`
for i in $TMP; do
    umount $i
done
