#!/bin/bash
###############################################################################
# gen-wrkspc.sh : Generates a chroot jail (ie workspace) & performs the mounts 
#
# Usage:
#   gen-workspace.sh NEW_WORKPACE_DIR [YUM_URL] [PACK]
#
###############################################################################

set -e

if [ -z "$UMD_TOOLS_PATH" ] ; then
    UMD_TOOLS_PATH="./developer-tools"
    echo "UMD_TOOLS_PATH is not defined!"
    echo -e "Using default value instead...\n"
fi

if [ ! -e $UMD_TOOLS_PATH ]; then
    echo -e "Error: UMD_TOOLS_PATH [${UMD_TOOLS_PATH}] not found!\n"
    exit -1
fi

workspace_dir=$1
yum_url="http://umd-repo.jf.intel.com/git/OpenSuSE10.2/binary-packages"
pack_to_install="${UMD_TOOLS_PATH}/packs/build-pack"

if [ -z "$workspace_dir" ]; then
    echo -e "USAGE: $0  NEW_WORKPACE_DIR [YUM_URL] [PACK]\n"
    exit -1
fi

if [ -e $workspace_dir ]; then
    echo "$workspace_dir already exist!"
    exit -1
fi

if [ ! -z "$2" ]; then
    yum_url="$2"
fi

if [ ! -z "$3" ]; then
    pack_to_install="$2"
fi

if [ `whoami` != "root" ]; then
    echo -e "ERROR: You have to be root to generate a new workspace!\n"
    exit -1
fi

echo "UMD_TOOLS_PATH   : ${UMD_TOOLS_PATH}"
echo "New workspace dir: ${workspace_dir}"
echo "Yum Repository   : ${yum_url}"
echo "Pack to install  : ${pack_to_install}"

echo -e "\nCreating workspace..."
${UMD_TOOLS_PATH}/scripts/create-workspace.sh ${workspace_dir} ${yum_url}

echo -e "\nInstalling pack..."
${UMD_TOOLS_PATH}/scripts/install-pack.sh ${pack_to_install} ${workspace_dir}

echo -e "\nMounting filesystems in workspace..."
${UMD_TOOLS_PATH}/scripts/mount-workspace.sh ${workspace_dir}

echo -e "\nFinished!\n"
