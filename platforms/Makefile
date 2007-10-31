DIRS = $(shell find -maxdepth 1 -type d | grep "..$*" | grep -v /common$)

all:
	@for i in ${DIRS}; do make -C $$i; done

install:
	@for i in ${DIRS}; do make -C $$i install; done

clean:
	@for i in ${DIRS}; do make -C $$i clean; done
