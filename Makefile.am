SUBDIRS = default_config gui help libs platforms po utils

ACLOCAL_AMFLAGS = -I m4

#EXTRA_DIST = config.rpath m4/ChangeLog  config.rpath m4/ChangeLog

executedir = ${sbindir}
execute_SCRIPTS = \
	image-creator

extradir = ${pkgdatadir}
extra_DATA = \
	COPYING

vardir = ${localstatedir}/lib/moblin-image-creator/projects
var_DATA = 

desktopdir = ${datadir}/applications
Desktop_Files = image-creator.desktop.in
desktop_DATA = $(Desktop_Files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

# We patch the path for the python modules post installation:
install-exec-hook:
	sed -i "s|@PATH_PKGDATADIR@|${pkgdatadir}|g" $(DESTDIR)$(sbindir)/image-creator
