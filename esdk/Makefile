all:

install:
	@mkdir -p /usr/share/esdk/{lib,platforms,projects}
	@cp *.py  /usr/share/esdk/lib
	@cp -a donley /usr/share/esdk/platforms/
	@cp project-builder /usr/sbin/
	@ln -f -s /usr/bin/consolehelper /usr/bin/project-builder
	@cp project-builder.pam.d /etc/pam.d/project-builder
	@cp project-builder.helperconsole /etc/security/console.apps/project-builder
	@cp *.glade /usr/share/esdk/

clean:
	rm -f *.pyc
	find -name \*~ -exec rm -f {} \;

cleanall: clean
	rm -rf /usr/share/esdk/lib
	rm -rf /usr/share/esdk/platforms
	rm -rf /usr/share/esdk/*.glade
