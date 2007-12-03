TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin-lpia-fedora
SHARE = ${DESTDIR}/usr/share/pdk
PLATFORM_DIR = ${SHARE}/platforms/${PNAME}

all:

install:
	@mkdir -p ${PLATFORM_DIR}
	@mkdir -p ${PLATFORM_DIR}/fsets
# Install common code to the platform first, so if we have platform
# specific code it will get overwritten.

# Platform specific code.
	@cp fsets/*.fset ${PLATFORM_DIR}/fsets/
clean:
	rm -f *.tar.bz2 *~ package-build-stamp
