TOOLS=squashfs-tools,busybox-initramfs,dosfstools,syslinux,module-init-tools,mtools,gpgv
TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin
SHARE = ${DESTDIR}/usr/share/pdk
PACKAGE_DIRS=$(shell find packages/ -maxdepth 1 -type d|grep "packages/..*")
PACKAGE_NAMES=$(shell  for p in ${PACKAGE_DIRS}; do grep 'Package:' $$p/debian/control|awk '{print $$2}'; done;)

all: build-rootstrap.tar.bz2 target-rootstrap.tar.bz2 package-build-stamp

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

build-rootstrap.tar.bz2:
	@echo "Creating build-rootstrap.tar.bz2..."
	@DEBOOTSTRAP_DIR=debootstrap/ debootstrap --arch i386 --variant=buildd --include=${TOOLS} $(shell cat build-codename) ${TMPDIR} $(shell cat build-mirror)
	@rm -fR ${TMPDIR}/var/cache/apt/archives/*.deb
	@cp sources/*.list ${TMPDIR}/etc/apt/sources.list.d/ || true
	@touch ${TMPDIR}/.buildroot
	@tar -jcpvf $@ -C ${TMPDIR} .
	@rm -fR ${TMPDIR}

target-rootstrap.tar.bz2:
	@echo "Creating target-rootstrap.tar.bz2..."
	@DEBOOTSTRAP_DIR=debootstrap/ debootstrap --arch i386 --include=apt $(shell cat target-codename) ${TMPDIR} $(shell cat target-mirror)
	@touch ${TMPDIR}/etc/kernel-img.conf
	@touch ${TMPDIR}/etc/kernel-pkg.conf
	@rm -fR ${TMPDIR}/var/cache/apt/archives/*.deb
	@cp sources/*.list ${TMPDIR}/etc/apt/sources.list.d/ || true
	@tar -jcpvf $@ -C ${TMPDIR} .
	@rm -fR ${TMPDIR}

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp buildroot.packages ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@mkdir -p ${SHARE}/platforms/${PNAME}/fsets
	@cp fsets/*.fset ${SHARE}/platforms/${PNAME}/fsets/
	@cp *-rootstrap.tar.bz2 ${SHARE}/platforms/${PNAME}/

clean-repo:
	@for p in ${PACKAGE_NAMES}; do \
		reprepro -b ../repo remove mobile $$p 2> /dev/null || true; \
	done
	rm -f package-build-stamp

clean:
	rm -f *.tar.bz2 *~ package-build-stamp

