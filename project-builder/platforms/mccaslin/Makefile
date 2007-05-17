TOOLS=squashfs-tools,busybox-initramfs,dosfstools,syslinux,module-init-tools,mtools

all: build-rootstrap.tar.bz2 target-rootstrap.tar.bz2

build-rootstrap.tar.bz2:
	@echo "Creating build-rootstrap.tar.bz2..."
	@debootstrap --variant=buildd --include=${TOOLS} --arch i386 $(shell cat build-codename) /tmp/.tmpbuilddir $(shell cat build-mirror)
	@tar -jcpvf $@ -C /tmp/.tmpbuilddir .

target-rootstrap.tar.bz2:
	@echo "Creating target-rootstrap.tar.bz2..."
	@debootstrap --arch i386 $(shell cat target-codename) /tmp/.tmpbuilddir $(shell cat target-mirror)
	@tar -jcpvf $@ -C /tmp/.tmpbuilddir .

clean:
	rm -f *.tar.bz2 *~

