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

# Check the path name. If the path is not absolute path, we need to convert 
# them to the absolute one first.
temp_target=`dirname $target`

while true
do
    if [ `dirname $temp_target` = $temp_target ]; then
        break
    fi
    export temp_target=`dirname $temp_target`
done

if [ "/" != $temp_target ]; then
    echo "$target is not an absolute path!"
    target=${PWD}/$target
    echo "fixed to $target"
fi

if [ `whoami` != "root" ]; then
    echo "You have to be root to install a software pack!"
    exit -1
fi

PACKAGES=`grep -v '^#' $pack|grep -v '^\W*$'`
for i in $PACKAGES; do
    yum -y --installroot=$target install $i
done
