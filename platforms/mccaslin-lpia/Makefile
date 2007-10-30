TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin-lpia
SHARE = ${DESTDIR}/usr/share/pdk

all:

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp -a initramfs ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}/fsets
	@cp fsets/*.fset ${SHARE}/platforms/${PNAME}/fsets/
	# Generic code install to the platform
	@cp ../generic/exclude ${SHARE}/platforms/${PNAME}
	@cp ../generic/install.sh ${SHARE}/platforms/${PNAME}
	@cp -a ../generic/sources ${SHARE}/platforms/${PNAME}
clean:
	rm -f *.tar.bz2 *~ package-build-stamp

