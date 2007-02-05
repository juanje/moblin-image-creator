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

if [[ ! $url =~ '.*://.*' ]]; then
    if [[ $url =~ '^/.*' ]]; then
	url="file://$url"
    else
	url="file://$PWD/$url"
    fi
fi

if [[ ! $workspace_dir =~ '^/.*' ]]; then
    workspace_dir="$PWD/$workspace_dir"
fi

if [ -e $workspace_dir ]; then
    echo "$workspace_dir already exist!"
    exit -1
fi

if [ `whoami` != "root" ]; then
    echo "You have to be root to create a new rootstrap!"
    exit -1
fi

##########################################################
## Create a yum configuration that uses the specified URL
##########################################################

mkdir -p $workspace_dir/etc/
cat > $workspace_dir/etc/yum.conf <<EOF
[main]
cachedir=/var/cache/yum
keepcache=0
debuglevel=2
logfile=/var/log/yum.log
pkgpolicy=newest
distroverpkg=redhat-release
tolerant=1
exactarch=1
obsoletes=1
gpgcheck=1
plugins=1
metadata_expire=1800
EOF

mkdir $workspace_dir/etc/yum.repos.d/
cat > $workspace_dir/etc/yum.repos.d/base.repo <<EOF
[Fodora Core 6]
name=Fedora Core 6 - Zod
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

# /dev/zero is needed to set file permissions.
mkdir -p $workspace_dir/dev/
mknod $workspace_dir/dev/null c 1 3
mknod $workspace_dir/dev/zero c 1 5

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
## Remove the default fedora yum repos
##########################################################

mkdir -p $workspace_dir/etc/yum.repos.d/backup
mv $workspace_dir/etc/yum.repos.d/fedora* $workspace_dir/etc/yum.repos.d/backup

##########################################################
## Perform final fixup on the workspace
##########################################################

rm $workspace_dir/dev/null
rm $workspace_dir/dev/zero


