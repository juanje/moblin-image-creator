TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin-lpia
SHARE = ${DESTDIR}/usr/share/pdk
PLATFORM_DIR = ${SHARE}/platforms/${PNAME}

all:

install:
	@mkdir -p ${PLATFORM_DIR}
	@mkdir -p ${PLATFORM_DIR}/fsets
# Install common code to the platform first, so if we have platform
# specific code it will get overwritten.
	@cp -a ../common/initramfs ${PLATFORM_DIR}/
	@cp -a ../common/sources ${PLATFORM_DIR}/
	@cp ../common/exclude ${PLATFORM_DIR}/
	@cp ../common/install.sh ${PLATFORM_DIR}/
# Platform specific code.
	@cp -a initramfs ${PLATFORM_DIR}/
	@cp fsets/*.fset ${PLATFORM_DIR}/fsets/
clean:
	rm -f *.tar.bz2 *~ package-build-stamp

