SHAREDIR = /usr/share/pdk/
VARDIR = /var/lib/moblin-image-creator

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
	@echo -n "Installing moblin-image-creator..."
	@mkdir -p ${DESTDIR}/${VARDIR}
	@mkdir -p ${DESTDIR}/${SHAREDIR}/default_config
	@mkdir -p ${DESTDIR}/${SHAREDIR}/lib
	@mkdir -p ${DESTDIR}/${SHAREDIR}/locale
	@mkdir -p ${DESTDIR}/${SHAREDIR}/projects
	@mkdir -p ${DESTDIR}/${SHAREDIR}/utils
	@head -n 1 debian/changelog > ${DESTDIR}/${SHAREDIR}/version
	@cp libs/*.py  ${DESTDIR}/${SHAREDIR}/lib
	@cp gui/*.py  ${DESTDIR}/${SHAREDIR}/lib
	@cp gui/*.glade ${DESTDIR}/${SHAREDIR}
	@cp gui/*.png ${DESTDIR}/${SHAREDIR}
	@cp gui/newFeature ${DESTDIR}/${SHAREDIR}
	@cp COPYING ${DESTDIR}/${SHAREDIR}/
	@cp -a gui/pixmaps/. ${DESTDIR}/${SHAREDIR}
	@cp default_config/defaults.cfg ${DESTDIR}/${SHAREDIR}/default_config/
	@mkdir -p ${DESTDIR}/usr/bin
	@rm -f ${DESTDIR}/usr/sbin/image-creator
	@cp image-creator ${DESTDIR}/usr/bin/
	@mkdir -p ${DESTDIR}/etc/bash_completion.d/
	@cp utils/image-creator-completion.bash ${DESTDIR}/etc/bash_completion.d/
	@mkdir -p ${DESTDIR}/${SHAREDIR}/gnome/help/image-creator/
	@cp -a help/* ${DESTDIR}/${SHAREDIR}/gnome/help/image-creator/
	@cp utils/*.py  ${DESTDIR}/${SHAREDIR}/utils/
	@mkdir -p ${DESTDIR}/usr/share/applications/
	sed '{s/%%EXEC_CMD%%/gksu \/usr\/bin\/image-creator/}' image-creator.desktop.template > ${DESTDIR}/usr/share/applications/image-creator.desktop
	@echo "Done"

rpm:
	@echo create the tarball...
	cd ..; cp -a moblin-image-creator moblin-image-creator-${VERSION}; tar zcpvf /usr/src/rpm/SOURCES/moblin-image-creator-${VERSION}.tgz moblin-image-creator-${VERSION}/; rm -fR moblin-image-creator-${VERSION}
	rpmbuild -bb moblin-image-creator.spec

# Cleans out the current directory cruft
clean:
	@echo -n "Cleaning up working directory files..."
	@rm -f *.pyc
	@rm -f unittest/*.pyc
	@find -name \*~ -exec rm -f {} \;
	@${MAKE} -C platforms clean
	@echo "Done"

# Cleans out the installation target
cleanall: clean
	@echo -n "Removing previously installed files..."
	@rm -rfv ${DESTDIR}/${VARDIR}/rootstraps
	@rm -rf ${DESTDIR}/${SHAREDIR}/gnome
	@rm -rf ${DESTDIR}/${SHAREDIR}/lib
	@rm -rf ${DESTDIR}/${SHAREDIR}/locale
	@rm -rf ${DESTDIR}/${SHAREDIR}/platforms
	@rm -f ${DESTDIR}/${SHAREDIR}/*.glade
	@rm -f ${DESTDIR}/usr/bin/image-creator
	@rm -f ${DESTDIR}/usr/sbin/image-creator
	@rm -f ${DESTDIR}/etc/bash_completion.d/image-creator-completion.bash
	@rm -rf ${DESTDIR}/${SHAREDIR}/utils
	@rm -f ${DESTDIR}/usr/share/applications/image-creator.desktop
	@echo "Done"

# Run the unit tests which run fairly quickly
runbasictests:
	@echo "Running basic unit tests..."
	unittest/testMoblin_apt.py
	unittest/test_fsets.py
	unittest/testProject.py
	unittest/testSdk.py
	@echo "Basic unit tests completed"

# Run all of our tests, even the ones that take a long time to run
runalltests: runtests
	@echo "Running unit tests that take a long time..."
	unittest/testInstallImage.py

uninstall: cleanall
	@echo "Uninstalling moblin-image-creator..."
	@rm -f ${DESTDIR}/${SHAREDIR}/*.png
	@rm -f ${DESTDIR}/${SHAREDIR}/*.xcf
	@rm -f ${DESTDIR}/${SHAREDIR}/*.xpm
	@rm -f ${DESTDIR}/${SHAREDIR}/README
	@rm -f ${DESTDIR}/${SHAREDIR}/COPYING
	@rm -f ${DESTDIR}/${SHAREDIR}/version
	@find ${DESTDIR}/${SHAREDIR}/projects -type f -exec echo Project found: {} \;
	@echo "Done"
