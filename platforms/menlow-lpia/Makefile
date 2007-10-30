PNAME = menlow-lpia
SHARE = ${DESTDIR}/usr/share/pdk

all:

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp -a initramfs ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}/fsets
	@cp fsets/*.fset ${SHARE}/platforms/${PNAME}/fsets/
	# Install common code to the platform
	@cp ../common/exclude ${SHARE}/platforms/${PNAME}
	@cp ../common/install.sh ${SHARE}/platforms/${PNAME}
	@cp -a ../common/sources ${SHARE}/platforms/${PNAME}
clean:
	rm -f *.tar.bz2 *~ package-build-stamp

