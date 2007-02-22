#!/bin/bash
#########################################################################################
# pkg-build.sh : Builds a source & binary rpm package inside a
#                workspace (i.e. chroot jail) and using src from
#                the package-meta-data and pristine-release-files dirs.
#
# Usage:
#   pkg-build.sh WORKSPACE_DIR PACKAGE_NAME [PACKAGE_META_DATA_DIR] [PRISTINE_SRC_DIR]
#
#########################################################################################

set -e

if [ -z "$1" ] || [ -z "$2" ] ; then
    echo -e "USAGE: $0 WORKSPACE_DIR PACKAGE_NAME [PACKAGE_META_DATA_DIR] [PRISTINE_SRC_DIR]\n"
    exit -1
fi

if [ -z "$UMD_DEV_PATH" ] ; then
    UMD_DEV_PATH="."
    echo "UMD_DEV_PATH is not defined!"
    echo -e "Using default value instead...\n"
fi

if [ ! -e $UMD_DEV_PATH ]; then
    echo -e "Error: UMD_DEV_PATH [${UMD_DEV_PATH}] not found!\n"
    exit -1
fi

if [ -z "$UMD_TOOLS_PATH" ] ; then
    UMD_TOOLS_PATH="${UMD_DEV_PATH}/developer-tools"
    echo "UMD_TOOLS_PATH is not defined!"
    echo -e "Using default value instead...\n"
fi

if [ ! -e $UMD_TOOLS_PATH ]; then
    echo -e "Error: UMD_TOOLS_PATH [${UMD_TOOLS_PATH}] not found!\n"
    exit -1
fi

workspace_dir=$1
pkg_name=$2

if [ ! -e $workspace_dir ]; then
    echo -e "Error: $workspace_dir doesn't exist!\n"
    exit -1
fi

if [ `whoami` != "root" ]; then
    echo -e "Error: You have to be root to build the SRPM inside a workspace!\n"
    exit -1
fi

if [ ! -z "$3" ]; then
    pkg_meta_data_dir="$3"
else
    pkg_meta_data_dir="${UMD_DEV_PATH}/package-meta-data"
fi

if [ ! -e $pkg_meta_data_dir ]; then
    echo -e "Error: $pkg_meta_dir does not exist!\n"
    exit -1
fi

if [ ! -z "$4" ]; then
    pristine_src_dir="$3"
else
    pristine_src_dir="${UMD_DEV_PATH}/pristine-release-files"
fi

if [ ! -e $pristine_src_dir ]; then
    echo -e "Error: $pkg_meta_dir does not exist!\n"
    exit -1
fi

# Find the first matching spec file for the named package
# WARNING: Can only have ONE spec file that matches this name in the tree.
spec_file=`find ${pkg_meta_data_dir} -name ${pkg_name}.spec -print -quit`
if [ -z "$spec_file" ]; then
    echo -e "Error: Unable to find the spec file for the ${pkg_name} package!\n"
    exit -1
fi

spec_pkg_name=`awk '/^Name:/ {print $2}' $spec_file`
pkg_group=`grep -m 1 ^Group: ${spec_file} | awk '{print $2}'`

# Sanity check the spec file vs. package name
if [ "$spec_pkg_name" != "$pkg_name" ] ; then
    echo -e "Error: Spec Pkg name [${spec_pkg_name}] doesn't match!\n"
    exit -1
fi

# Check for location of the RPM directory within the workspace
if [ -d ${workspace_dir}/usr/src/redhat ] ; then
    # Location for a RedHat/Fedora System
    rpm_root="/usr/src/redhat"
elif [ -d ${workspace_dir}/usr/src/packages ] ; then
    # Location for a Novell SuSE System
    rpm_root="/usr/src/packages"
else
    # Houstan, we have a problem...
    echo -e "Error: Unable to find the RPM directory within the workspace [${workspace_dir}]!\n"
    exit -1
fi

rpm_dir="${workspace_dir}${rpm_root}"

echo "UMD_DEV_PATH      : ${UMD_DEV_PATH}"
echo "UMD_TOOLS_PATH    : ${UMD_TOOLS_PATH}"
echo "Workspace Dir     : ${workspace_dir}"
echo "Package Meta Dir  : ${pkg_meta_data_dir}"
echo "Pristine Src Dir  : ${pristine_src_dir}"
echo
echo "Spec File         : ${spec_file}"
echo "Package Name      : ${pkg_name}"
echo "Package Group     : ${pkg_group}"
echo "RPM Package Dir   : ${rpm_dir}"

echo -e "\nCopying source files to workspace..."
cp -fv ${pkg_meta_data_dir}/${pkg_group}/${pkg_name}/files/* \
       ${rpm_dir}/SOURCES

echo -e "\nCopying pristine release files to workspace..."
cp -fv ${pristine_src_dir}/${pkg_group}/${pkg_name}/* \
       ${rpm_dir}/SOURCES

echo -e "\nCopying spec files to workspace..."
cp -fv ${spec_file} ${rpm_dir}/SPECS

echo -e "\nLaunching build inside workspace..."
/usr/sbin/chroot ${workspace_dir} rpmbuild -bs ${rpm_root}/SPECS/${pkg_name}.spec
/usr/sbin/chroot ${workspace_dir} rpmbuild -bb ${rpm_root}/SPECS/${pkg_name}.spec

echo -e "\nFinished!\n"
