TOOLS=squashfs-tools,busybox-initramfs,dosfstools,syslinux,module-init-tools,mtools,gpgv
TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin
SHARE = ${DESTDIR}/usr/share/pdk
PACKAGE_DIRS=$(shell find packages/ -maxdepth 1 -type d|grep "packages/..*")
PACKAGE_NAMES=$(shell  for p in ${PACKAGE_DIRS}; do grep 'Package:' $$p/debian/control|awk '{print $$2}'; done;)

all: package-build-stamp

package-build-stamp:
	@for p in ${PACKAGE_DIRS}; do \
		cd $$p; \
		dpkg-buildpackage -us -uc -b -rfakeroot; \
		cd -; \
	done
	${MAKE} import-packages
	@touch package-build-stamp

import-packages:
	@for p in $(shell find packages/ -name '*.deb'); do \
		reprepro -b ../repo/ includedeb mobile $$p || true; \
	done

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp buildroot.packages ${SHARE}/platforms/${PNAME}
	@cp exclude ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp -a sources ${SHARE}/platforms/${PNAME}
	@cp -a initramfs ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}/fsets
	@cp fsets/*.fset ${SHARE}/platforms/${PNAME}/fsets/
	@cp *cmdline* ${SHARE}/platforms/${PNAME}/
	@cp buildroot_extras ${SHARE}/platforms/${PNAME}/
	@cp *-mirror ${SHARE}/platforms/${PNAME}/ 2> /dev/null || true
	@cp *-codename ${SHARE}/platforms/${PNAME}/ 2> /dev/null || true

clean-repo:
	@for p in ${PACKAGE_NAMES}; do \
		reprepro -b ../repo remove mobile $$p 2> /dev/null || true; \
	done
	rm -f package-build-stamp

clean:
	rm -f *.tar.bz2 *~ package-build-stamp

