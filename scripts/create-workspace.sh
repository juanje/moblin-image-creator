#!/bin/bash
###############################################################################
# create-workspace.sh : Creates a fundamental workspace capabile of
#                       chroot'ing inside and using yum to install additional
#                       packages
###############################################################################

# absolute path to new directory for creating workspace
workspace_dir=$1
shift

# top level packages to install in the rootstrap image. Yum will automatically
# perform dependency resolution
PACKAGES="util-linux rpm yum"

if [ -z "$workspace_dir" ] || [ -z "$1" ]; then
    echo "USAGE: $0 NEW_WORKSPACE_DIR YUM_URL1 [YUM_URL2] [...]"
    exit -1
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

COUNT=0
mkdir $workspace_dir/etc/yum.repos.d/
while [ "$#" -ne "0" ] ; do
	url="$1"
	shift

	if [[ ! $url =~ '.*://.*' ]]; then
	    if [[ $url =~ '^/.*' ]]; then
		url="file://$url"
	    else
		url="file://$PWD/$url"
	    fi
	fi

	cat > $workspace_dir/etc/yum.repos.d/$COUNT.repo <<EOF
[Repository #$COUNT]
name=Repository-$url
baseurl=$url
enabled=1
gpgcheck=0
EOF

	((COUNT++))
done

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
## Import the signing keys for the repository
##########################################################

rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-fedora
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-extras

##########################################################
## Perform final fixup on the workspace
##########################################################

rm $workspace_dir/dev/null
rm $workspace_dir/dev/zero


