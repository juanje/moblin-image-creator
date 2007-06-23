SHARE = ${DESTDIR}/usr/share/pdk
DIRS = $(shell find -maxdepth 1 -type d|grep "..$*"|grep -v "repo")

all:
	@for i in ${DIRS}; do make -C $$i; done

install:
	@for i in ${DIRS}; do make -C $$i install; done
	@if [ -d ${SHARE}/repo ]; then rm -fR ${SHARE}/repo; fi
	@cp -a repo ${SHARE}/repo

clean:
	@for i in ${DIRS}; do make -C $$i clean; done
	@rm -fR repo/db repo/dists repo/pool


