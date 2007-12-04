TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin-lpia-fedora
SHARE = ${DESTDIR}/usr/share/pdk
PLATFORM_DIR = ${SHARE}/platforms/${PNAME}

all:

install:
	@mkdir -p ${PLATFORM_DIR}
	@mkdir -p ${PLATFORM_DIR}/fsets
	@mkdir -p ${PLATFORM_DIR}/yum.repos.d
# Install common code to the platform first, so if we have platform
# specific code it will get overwritten.

# Platform specific code.
	@cp fsets/*.fset ${PLATFORM_DIR}/fsets/
	@cp yum.repos.d/* ${PLATFORM_DIR}/yum.repos.d/
clean:
	rm -f *.tar.bz2 *~ package-build-stamp
