SHAREDIR = /usr/share/pdk/

VERSION = 0.1
all:
	${MAKE} -C platforms

# This target will do a cleanall and then reinstall
cleaninstall: cleanall install

# Simple tests
runtests: runbasictests

# Everytime we install the code we want the basic unit tests to run
install: basicinstall runbasictests

basicinstall: all
	@echo "Installing platform definitions..."
	@${MAKE} -C platforms install
	@echo -n "Installing project-builder..."
	@mkdir -p ${DESTDIR}/${SHAREDIR}/lib
	@mkdir -p ${DESTDIR}/${SHAREDIR}/locale
	@mkdir -p ${DESTDIR}/${SHAREDIR}/projects
	@mkdir -p ${DESTDIR}/${SHAREDIR}/utils
	@if [ ! -f ${DESTDIR}/usr/lib/debootstrap/scripts/gutsy ]; then \
		mkdir -p ${DESTDIR}/usr/lib/debootstrap/scripts; \
		cp utils/gutsy ${DESTDIR}/usr/lib/debootstrap/scripts/; \
	fi
	@cp libs/*.py  ${DESTDIR}/${SHAREDIR}/lib
	@cp gui/*.py  ${DESTDIR}/${SHAREDIR}/lib
	@cp gui/*.glade ${DESTDIR}/${SHAREDIR}
	@cp COPYING ${DESTDIR}/${SHAREDIR}/
	@cp -a gui/pixmaps/ ${DESTDIR}/${SHAREDIR}
	@mkdir -p ${DESTDIR}/usr/sbin
	@cp project-builder ${DESTDIR}/usr/sbin/
	@mkdir -p ${DESTDIR}/etc/bash_completion.d/
	@cp utils/project-builder-completion.bash ${DESTDIR}/etc/bash_completion.d/
	@mkdir -p ${DESTDIR}/${SHAREDIR}/gnome/help/project-builder/
	@cp -a help/* ${DESTDIR}/${SHAREDIR}/gnome/help/project-builder/
	@cp utils/*.py  ${DESTDIR}/${SHAREDIR}/utils/
	@mkdir -p ${DESTDIR}/usr/share/applications/
	sed '{s/%%EXEC_CMD%%/gksu \/usr\/sbin\/project-builder/}' project-builder.desktop.template > ${DESTDIR}/usr/share/applications/project-builder.desktop
	@echo "Done"

rpm:
	@echo create the tarball...
	cd ..; cp -a project-builder project-builder-${VERSION}; tar zcpvf /usr/src/rpm/SOURCES/project-builder-${VERSION}.tgz project-builder-${VERSION}/; rm -fR project-builder-${VERSION}
	rpmbuild -bb project-builder.spec

# Cleans out the current directory cruft
clean:
	@echo -n "Cleaning up working directory files..."
	@rm -f *.pyc
	@rm -f unittest/*.pyc
	@find -name \*~ -exec rm -f {} \;
	@echo "Done"

# Cleans out the installation target
cleanall: clean
	@${MAKE} -C platforms clean
	@echo -n "Removing previously installed files..."
	@rm -rf ${DESTDIR}/${SHAREDIR}/gnome
	@rm -rf ${DESTDIR}/${SHAREDIR}/lib
	@rm -rf ${DESTDIR}/${SHAREDIR}/locale
	@rm -rf ${DESTDIR}/${SHAREDIR}/platforms
	@rm -f ${DESTDIR}/${SHAREDIR}/*.glade
	@rm -f ${DESTDIR}/usr/bin/project-builder
	@rm -f ${DESTDIR}/usr/sbin/project-builder
	@rm -f ${DESTDIR}/etc/bash_completion.d/project-builder-completion.bash
	@rm -rf ${DESTDIR}/${SHAREDIR}/utils
	@rm -f ${DESTDIR}/usr/share/applications/project-builder.desktop
	@echo "Done"

# Run the unit tests which run fairly quickly
runbasictests:
	@echo "Running basic unit tests..."
	unittest/test_fsets.py
	unittest/testProject.py
	unittest/testSdk.py
	@echo "Basic unit tests completed"

# Run all of our tests, even the ones that take a long time to run
runalltests: runtests
	@echo "Running unit tests that take a long time..."
	unittest/testInstallImage.py

