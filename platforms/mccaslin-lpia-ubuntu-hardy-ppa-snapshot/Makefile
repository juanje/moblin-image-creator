TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin-lpia-ubuntu-hardy-ppa-snapshot
SHARE = ${DESTDIR}/usr/share/pdk
PLATFORM_DIR = ${SHARE}/platforms/${PNAME}

all:

install:
	@mkdir -p ${PLATFORM_DIR}
	@mkdir -p ${PLATFORM_DIR}/fsets
	@mkdir -p ${PLATFORM_DIR}/initramfs/scripts
# Install common code to the platform first, so if we have platform
# specific code it will get overwritten.
	@cp -a ../common-apt/initramfs ${PLATFORM_DIR}/
	@cp ../common-apt/exclude ${PLATFORM_DIR}/
	@cp ../common-apt/install.sh ${PLATFORM_DIR}/
# Platform specific code.
	@cp -a sources ${PLATFORM_DIR}/
	@cp -a initramfs ${PLATFORM_DIR}/
	@cp fsets/*.fset ${PLATFORM_DIR}/fsets/
clean:
	rm -f *.tar.bz2 *~ package-build-stamp

