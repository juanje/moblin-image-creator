all:

# This target will do a cleanall and then reinstall
cleaninstall: cleanall install
# Same as cleaninstall
runtests: cleaninstall

# Everytime we install the code we want the basic unit tests to run
install: basicinstall runbasictests

basicinstall:
	@echo -n "Installing project-builder..."
	@mkdir -p /usr/share/esdk/{lib,platforms,projects}
	@cp *.py  /usr/share/esdk/lib
	@cp -a platforms/* /usr/share/esdk/platforms/
	@cp *.glade /usr/share/esdk/
	@cp project-builder /usr/sbin/
	@cp ReleaseNotes.txt /usr/share/esdk/
	@if [ -d /etc/security/console.apps ]; then \
		ln -f -s /usr/bin/consolehelper /usr/bin/project-builder; \
		cp project-builder.pam.d /etc/pam.d/project-builder; \
		cp project-builder.helperconsole /etc/security/console.apps/project-builder; \
	else \
		cp project-builder-launcher /usr/bin/project-builder; \
	fi
	@if [ ! -d /etc/bash_completion.d/ ]; then \
	    mkdir /etc/bash_completion.d; \
	fi
	@cp project-builder-completion.bash /etc/bash_completion.d/
	@echo "Done"

# Cleans out the current directory cruft
clean:
	@rm -f *.pyc
	@rm -f unittest/*.pyc
	@find -name \*~ -exec rm -f {} \;

# Cleans out the installation target
cleanall: clean
	@rm -rf /usr/share/esdk/lib
	@rm -rf /usr/share/esdk/platforms
	@rm -rf /usr/share/esdk/*.glade
	@rm -f /usr/bin/project-builder
	@rm -f /usr/sbin/project-builder

# Run the unit tests which run fairly quickly
runbasictests:
	@echo "Running basic unit tests..."
	unittest/testFSet.py
	unittest/testPlatform.py
	unittest/testProject.py
	unittest/testSdk.py
	@echo "Basic unit tests completed"

# Run all of our tests, even the ones that take a long time to run
runalltests: runtests
	@echo "Running unit tests that take a long time..."
	unittest/testInstallImage.py
