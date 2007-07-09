TOOLS=squashfs-tools,busybox-initramfs,dosfstools,syslinux,module-init-tools,mtools,gpgv
TMPDIR = /tmp/.tmpbuilddir
PNAME = menlow
SHARE = ${DESTDIR}/usr/share/pdk

all:

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp buildroot.packages ${SHARE}/platforms/${PNAME}
	@cp exclude ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp -a sources ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}/fsets
	@cp fsets/*.fset ${SHARE}/platforms/${PNAME}/fsets/
	@cp *cmdline* ${SHARE}/platforms/${PNAME}/
	@cp buildroot_extras ${SHARE}/platforms/${PNAME}/
	@cp *-mirror ${SHARE}/platforms/${PNAME}/ 2> /dev/null || true
	@cp *-codename ${SHARE}/platforms/${PNAME}/ 2> /dev/null || true

clean:
	rm -f *.tar.bz2 *~

