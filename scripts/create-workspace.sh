#!/bin/bash
###############################################################################
# create-workspace.sh : Creates a fundamental workspace capabile of
#                       chroot'ing inside and using yum to install additional
#                       packages
###############################################################################

set -e

# absolute path to new directory for creating workspace
workspace_dir=$1

# URL to yum repository. Note that using a file:/// URL will work in creating
# the rootstrap, but then yum will not be usable inside the resulting workspace
# untill either the yum repository is made available in the same absolute
# location inside the workspace (like by mounting a portion of the filesystem 
# using the --bind argument), or by changing the baseurl in the yum config.
url=$2

# top level packages to install in the rootstrap image. Yum will automatically
# perform dependency resolution
PACKAGES="util-linux rpm yum"

if [ -z "$workspace_dir" ] || [ -z "$url" ]; then
    echo "USAGE: $0 NEW_WORKSPACE_DIR YUM_URL"
    exit -1
fi

# Check the path name. If the path is not absolute path, we need to convert 
# them to the absolute one first.
temp_dir=`dirname $workspace_dir`
temp_url=`dirname $url`

while true
do
    if [ `dirname $temp_dir` = $temp_dir ] && [ `dirname $temp_url` = $temp_url ]; then
        break
    fi
    export temp_dir=`dirname $temp_dir`
    export temp_url=`dirname $temp_url`
done

if [ "/" != $temp_dir ]; then
    echo "$workspace_dir is not an absolute path!"
    workspace_dir=${PWD}/$workspace_dir
    echo "fixed to $workspace_dir"
fi

if [ "/" != $temp_url ]; then
    echo "$url is not an absolute path!"
    url=${PWD}/$url
    echo "fixed to $url"
fi

if [ -e $workspace_dir ]; then
    echo "$workspace_dir already exist!"
    exit -1
fi

if [ `whoami` != "root" ]; then
    echo "You have to be root to create a new rootstrap!"
    exit -1
fi

# Check the base url comfort. If it is only a local path, insert "file://" in the head.
if [ -z `echo $url | grep file:///` ] && [ -z `echo $url | grep http://` ]; then
    url="file://$url"
    echo "Insert header, fixed to $url"
fi

# TODO: Either enforce that the workspace_dir is an absolute path
#       or automatically convert it to an absolute path.  Yum expects
#       an absolute path for it's rootinstall argument and fails in
#       a most ungraceful mannor if you pass it anything less.

##########################################################
## Create a yum configuration that uses the specified URL
##########################################################

mkdir -p $workspace_dir/etc/
cat > $workspace_dir/etc/yum.conf <<EOF
[main]
cachedir=/var/cache/yum
reposdir=/etc/yum.repos.d
debuglevel=2
errorlevel=2
logfile=/var/log/yum.log
gpgcheck=0
assumeyes=0
tolerant=1
exactarch=1
obsoletes=1
distroverpkg=suse-release
retries=20
pkgpolicy=newest
EOF

mkdir $workspace_dir/etc/yum.repos.d/
cat > $workspace_dir/etc/yum.repos.d/base.repo <<EOF
[sled10]
name=SLED 10
baseurl=$url
enabled=1
gpgcheck=0
EOF

##########################################################
## Final fixup before calling yum
##########################################################

# If we don't create /dev/null then various packages 
# will waste their time redirecting thier output to a real file
# located at /dev/null
mkdir -p $workspace_dir/dev/
mknod $workspace_dir/dev/null c 1 3

# Carry over the creators basic system configuration
cp /etc/hosts $workspace_dir/etc/
cp /etc/passwd $workspace_dir/etc/
cp /etc/group $workspace_dir/etc/
cp /etc/resolv.conf $workspace_dir/etc/

mkdir -p $workspace_dir/proc/

##########################################################
## Install the minimal set workspace packages
##########################################################
mkdir -p $workspace_dir/var/lib/rpm
yum -y --installroot=$workspace_dir install $PACKAGES

##########################################################
## Perform final fixup on the workspace
##########################################################

rm $workspace_dir/dev/null

