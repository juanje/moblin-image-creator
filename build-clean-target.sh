#!/bin/bash

PROJECT=$1
shift

PLATFORM=$1
shift

PPATH=$1
shift

FSET=$1
shift

IMAGE=$1
shift 

if [ "`/usr/bin/whoami`" != "root" ]; then
    echo "You must be root to run this script!"
    exit 1
fi

if [ -z "${PROJECT}" ] || [ -z "${PLATFORM}" ] || [ -z "${PPATH}" ] || [ -z "${FSET}" ]; then
    echo ""
    echo "USAGE: $0 projectname platformname path fset [image-name | 'xephyr']"
    echo "       projectname       Name of project"
    echo "       platformname      menlow-lpia or mccaslin-lpia" 
    echo "       path              Destination directory (needs ~1.5GB free, or ~2GB if creating image)"
    echo "       fset              e.g. samsung-full-mobile-stack or crownBeach-full-mobile-stack"
    echo "       image | 'xephyr'  Name of image file OR 'xephyr' to skip image creation and start xephyr"
    echo ""
    exit 1
fi

if [ -z "${IMAGE}" ]; then
    echo -e "\033[1m No image file name given.  Image will NOT be created.\033[0m"
fi


if [ -e ${PPATH} ]; then
    echo "ERROR: Path already exists!"
    exit 1
fi

for i in `image-creator -c list-projects`; do
    if [ $i = ${PROJECT} ]; then
	echo "ERROR: A project called ${PROJECT} already exists!"
	exit 1
    fi
done

FOUND=0
for i in `image-creator -c list-platforms`; do
    if [ $i = ${PLATFORM} ]; then
	FOUND=1
    fi
done
if [ ${FOUND} -eq 0 ]; then
    echo "ERROR: A platform of the name ${PLATFORM} does not exists!"
    echo "Available platforms include:"
    image-creator -c list-platforms
    exit 1
fi

FOUND=0
for i in `image-creator -c list-fsets --platform-name ${PLATFORM}`; do
    if [ $i = ${FSET} ]; then
	FOUND=1
    fi
done
if [ ${FOUND} -eq 0 ]; then
    echo "ERROR: A fset of the name ${FSET} does not exists!"
    echo "Available fsets include:"
    image-creator -c list-fsets --platform-name ${PLATFORM}
    exit 1
fi

echo "Building..."
echo -e "\tPlatform = ${PLATFORM}"
echo -e "\tPROJECT = ${PROJECT}"
echo -e "\tPPATH = ${PPATH}"
echo -e "\tFSET = ${FSET}"
echo -e "\tIMAGE = ${IMAGE}"

echo "Creating a new project..."
image-creator -c create-project                                 \
                        --project-name ${PROJECT}                         \
                        --project-description "Clean build of ${PROJECT}" \
                        --project-path ${PPATH}                            \
                        --platform-name ${PLATFORM}                       \
                        --bypass-rootstrap
if [ $? != 0 ]; then
    echo "Bailing out on project creation error!"
    exit 1
fi
echo "Successfully created project '${PROJECT}'"

echo "Creating a new target..."
image-creator -c create-target          \
                        --project-name ${PROJECT} \
                        --target-name "test"      \
                        --bypass-rootstrap
if [ $? != 0 ]; then
    echo "Bailing out on target creation error!"
    exit 1
fi
echo "Successfully created target 'test'"

echo "Installing a new fset..."
image-creator -c install-fset           \
                        --project-name ${PROJECT} \
                        --target-name "test"      \
                        --fset-name ${FSET}
if [ $? != 0 ]; then
    echo "Bailing out on fset install error!"
    exit 1
fi
echo "Successfully installed FSET '${FSET}'"

if [ -z "${IMAGE}" ]; then
    echo "No image specified.  None created."
    exit 1
fi
if [ ${IMAGE} == 'xephyr' ]; then
    xhost +SI:localuser:root
    image-creator --command run-target --project-name ${PROJECT} --target-name test --run-command ume-xephyr-start
    exit 1
fi

echo "Creating a new install USB key..."
image-creator -c create-install-usb     \
                        --project-name ${PROJECT} \
                        --target-name "test"      \
                        --image-name ${IMAGE}
if [ $? != 0 ]; then
    echo "Bailing out on usb install creation error!"
    exit 1
fi
echo "Succesfully built a USB install image at:"
echo "${PPATH}/targets/test/fs/image/${IMAGE}"


