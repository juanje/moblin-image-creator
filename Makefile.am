SUBDIRS = default_config gui help libs platforms po utils

ACLOCAL_AMFLAGS = -I m4

#EXTRA_DIST = config.rpath m4/ChangeLog  config.rpath m4/ChangeLog

executedir = ${bindir}
execute_SCRIPTS = \
	image-creator

extradir = ${pkgdatadir}
extra_DATA = \
	COPYING

vardir = ${localstatedir}/lib/moblin-image-creator
var_DATA = \
	.empty

desktopdir = ${datadir}/applications
Desktop_Files = image-creator.desktop.in
desktop_DATA = $(Desktop_Files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@
