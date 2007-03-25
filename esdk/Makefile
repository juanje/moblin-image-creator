all:

install:
	@mkdir -p /usr/share/esdk/{lib,platforms,projects}
	@cp *.py  /usr/share/esdk/lib
	@cp -a platforms/* /usr/share/esdk/platforms/
	@cp *.glade /usr/share/esdk/
	@cp project-builder /usr/sbin/
	if [ -z "$(shell which gnomesu 2> /dev/null)" ]; then \
		echo "Installing consolehelper..."; \
		ln -f -s /usr/bin/consolehelper /usr/bin/project-builder; \
		cp project-builder.pam.d /etc/pam.d/project-builder; \
		cp project-builder.helperconsole /etc/security/console.apps/project-builder; \
	else \
		echo "Installing launcher..."; \
		cp project-builder-launcher /usr/bin/project-builder; \
	fi

clean:
	@rm -f *.pyc
	@find -name \*~ -exec rm -f {} \;

cleanall: clean
	@rm -rf /usr/share/esdk/lib
	@rm -rf /usr/share/esdk/platforms
	@rm -rf /usr/share/esdk/*.glade
	@rm -f /usr/bin/project-builder
	@rm -f /usr/sbin/project-builder
