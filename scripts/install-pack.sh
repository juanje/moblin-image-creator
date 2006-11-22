#!/bin/bash
###############################################################################
# install_pack.sh
###############################################################################

set -e

pack=$1
target=$2

if [ -z "$pack" ] || [ -z "$target" ]; then
    echo "USAGE: $0 PACK TARGET_DIR"
    exit -1
fi

if [ ! -d $target ]; then
    echo "$target does not exist!"
    exit -1
fi

if [ `whoami` != "root" ]; then
    echo "You have to be root to install a software pack!"
    exit -1
fi

PACKAGES=`grep -v '^#' $pack|grep -v '^\W*$'`
for i in $PACKAGES; do
    yum -y --installroot=$target install $i
done
