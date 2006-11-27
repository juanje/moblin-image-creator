#!/bin/bash
###############################################################################
# prepare_workspace.sh : Creates a new workspace from an existing rootstrap
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
    echo "You have to be root to mount a workspace!"
    exit -1
fi


mount --bind /proc $target/proc
mount --bind /tmp $target/tmp
mount --bind /sys $target/sys
mount --bind /dev $target/dev

# If a local (i.e. file:// based URL) yum repository was used, then
# bind the appropriate directory inside the new workspace so that 
# yum can still be used in the way
TMP=`grep baseurl $target/etc/yum.repos.d/*.repo|awk -Ffile:// '{print $2}'`
for i in $TMP; do
    mkdir -p $target$i
    mount --bind $i $target$i
done
