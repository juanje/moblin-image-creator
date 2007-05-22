TOOLS=squashfs-tools,busybox-initramfs,dosfstools,syslinux,module-init-tools,mtools,gpgv
TMPDIR = /tmp/.tmpbuilddir
PNAME = mccaslin
SHARE = /usr/share/pdk

all: build-rootstrap.tar.bz2 target-rootstrap.tar.bz2

build-rootstrap.tar.bz2:
	@echo "Creating build-rootstrap.tar.bz2..."
	@debootstrap --variant=buildd --include=${TOOLS} --arch i386 $(shell cat build-codename) ${TMPDIR} $(shell cat build-mirror)
	@rm -fR ${TMPDIR}/var/cache/apt/archives/*.deb
	@cp build-sources/*.list ${TMPDIR}/etc/apt/sources.list.d/ || true
	@touch ${TMPDIR}/.buildroot
	@tar -jcpvf $@ -C ${TMPDIR} .
	@rm -fR ${TMPDIR}

target-rootstrap.tar.bz2:
	@echo "Creating target-rootstrap.tar.bz2..."
	@debootstrap --arch i386 $(shell cat target-codename) ${TMPDIR} $(shell cat target-mirror)
	@rm -fR ${TMPDIR}/var/cache/apt/archives/*.deb
	@cp target-sources/*.list ${TMPDIR}/etc/apt/sources.list.d/ || true
	@tar -jcpvf $@ -C ${TMPDIR} .
	@rm -fR ${TMPDIR}

install:
	@mkdir -p ${SHARE}/platforms/${PNAME}
	@cp buildroot.packages ${SHARE}/platforms/${PNAME}
	@cp -a fsets ${SHARE}/platforms/${PNAME}/
	@mkdir -p /usr/lib/debootstrap/scripts/
	@cp gutsy /usr/lib/debootstrap/scripts/
	@cp *-rootstrap.tar.bz2 ${SHARE}/platforms/${PNAME}/

clean:
	rm -f *.tar.bz2 *~

