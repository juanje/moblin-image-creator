SHELL="/bin/bash"
SHAREDIR=/usr/share/pdk/

ROOTSTRAP_FILES = platforms/zi9/rootstrap.tar.bz2 \
                  platforms/donley/rootstrap.tar.bz2 \
                  platforms/menlow/rootstrap.tar.bz2

all:

# This target will do a cleanall and then reinstall
cleaninstall: cleanall install

# Same as cleaninstall
runtests: cleaninstall

# Everytime we install the code we want the basic unit tests to run
install: basicinstall runbasictests

basicinstall: ${ROOTSTRAP_FILES}
	@echo -n "Installing project-builder..."
	@mkdir -p ${DESTDIR}/${SHAREDIR}{lib,platforms,projects,utils}
	@cp libs/*.py  ${DESTDIR}/${SHAREDIR}/lib
	@cp gui/*.py  ${DESTDIR}/${SHAREDIR}/lib
	@cp -a platforms/* ${DESTDIR}/${SHAREDIR}/platforms/
	@cp gui/*.glade ${DESTDIR}/${SHAREDIR}
	@cp COPYING ${DESTDIR}/${SHAREDIR}/
	@mkdir -p ${DESTDIR}/usr/{bin,sbin}
	@cp project-builder ${DESTDIR}/usr/sbin/
	@ln -f -s /usr/bin/consolehelper ${DESTDIR}/usr/bin/project-builder
	@mkdir -p ${DESTDIR}/etc/pam.d
	@mkdir -p ${DESTDIR}/etc/security/console.apps
	@cp project-builder.pam.d ${DESTDIR}/etc/pam.d/project-builder
	@cp project-builder.helperconsole ${DESTDIR}/etc/security/console.apps/project-builder
	@mkdir -p ${DESTDIR}/etc/bash_completion.d/
	@cp utils/project-builder-completion.bash ${DESTDIR}/etc/bash_completion.d/
	@mkdir -p ${DESTDIR}/${SHAREDIR}/gnome/help/project-builder/
	@cp -a help/* ${DESTDIR}/${SHAREDIR}/gnome/help/project-builder/
	@cp utils/*.py  ${DESTDIR}/${SHAREDIR}/utils/
	@echo "Done"

platforms/donley/rootstrap.tar.bz2:
	@./utils/create-rootstrap.py  platforms/donley

platforms/zi9/rootstrap.tar.bz2:
	@./utils/create-rootstrap.py  platforms/zi9

platforms/menlow/rootstrap.tar.bz2:
	@./utils/create-rootstrap.py  platforms/menlow

# Cleans out the current directory cruft
clean:
	@echo -n "Cleaning up working directory files..."
	@rm -f *.pyc
	@rm -f unittest/*.pyc
	@find -name \*~ -exec rm -f {} \;
	@rm -f ${ROOTSTRAP_FILES}
	@echo "Done"

# Cleans out the installation target
cleanall: clean
	@echo -n "Removing previously installed files..."
	@rm -rf ${DESTDIR}/${SHAREDIR}/lib
	@rm -rf ${DESTDIR}/${SHAREDIR}/platforms
	@rm -rf ${DESTDIR}/${SHAREDIR}/gnome
	@rm -f ${DESTDIR}/${SHAREDIR}/*.glade
	@rm -f ${DESTDIR}/usr/bin/project-builder
	@rm -f ${DESTDIR}/usr/sbin/project-builder
	@rm -f ${DESTDIR}/etc/bash_completion.d/project-builder-completion.bash
	@rm -rf ${DESTDIR}/${SHAREDIR}/utils
	@echo "Done"

# Run the unit tests which run fairly quickly
runbasictests:
	@echo "Running basic unit tests..."
	unittest/test_fsets.py
	unittest/testPlatform.py
	unittest/testProject.py
	unittest/testSdk.py
	@echo "Basic unit tests completed"

# Run all of our tests, even the ones that take a long time to run
runalltests: runtests
	@echo "Running unit tests that take a long time..."
	unittest/testInstallImage.py
