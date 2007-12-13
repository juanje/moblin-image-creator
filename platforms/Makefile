SHARE = ${DESTDIR}/usr/share/pdk
PLATFORM_DIR = ${SHARE}/platforms/
DIRS = $(shell find -maxdepth 1 -type d | grep "..$*" | grep -v /common)

all:
	echo ${DIRS}
	@for i in ${DIRS}; do make -C $$i; done

install:
	@mkdir -p ${SHARE}/debootstrap-scripts
	@cp common-apt/debootstrap-scripts/* ${SHARE}/debootstrap-scripts/
	@for i in ${DIRS}; do make -C $$i install; done
	@cp -a platforms.cfg ${PLATFORM_DIR}/

clean:
	@for i in ${DIRS}; do make -C $$i clean; done
