PNAME = menlow-lpia
SHARE = ${DESTDIR}/usr/share/pdk

all:

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp install.sh ${SHARE}/platforms/${PNAME}
	@cp exclude ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp -a sources ${SHARE}/platforms/${PNAME}
	@cp -a initramfs ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}/fsets
	@cp fsets/*.fset ${SHARE}/platforms/${PNAME}/fsets/

clean:
	rm -f *.tar.bz2 *~ package-build-stamp

