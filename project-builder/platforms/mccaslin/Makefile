TOOLS=squashfs-tools,busybox-initramfs,dosfstools,syslinux,module-init-tools,mtools
TMPDIR = /tmp/.tmpbuilddir

all: build-rootstrap.tar.bz2 target-rootstrap.tar.bz2

build-rootstrap.tar.bz2:
	@echo "Creating build-rootstrap.tar.bz2..."
	@debootstrap --variant=buildd --include=${TOOLS} --arch i386 $(shell cat build-codename) ${TMPDIR} $(shell cat build-mirror)
	@rm -fR ${TMPDIR}/var/cache/apt
	@tar -jcpvf $@ -C ${TMPDIR} .
	@rm -fR ${TMPDIR}

target-rootstrap.tar.bz2:
	@echo "Creating target-rootstrap.tar.bz2..."
	@debootstrap --arch i386 $(shell cat target-codename) ${TMPDIR} $(shell cat target-mirror)
	@rm -fR ${TMPDIR}/var/cache/apt
	@tar --exclude="var/cache/apt/" -jcpvf $@ -C ${TMPDIR} .
	@rm -fR ${TMPDIR}

clean:
	rm -f *.tar.bz2 *~

