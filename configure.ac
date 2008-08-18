#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.61)
AC_INIT(pdk, 0.45, mamano@miraclelinux.com)
AM_INIT_AUTOMAKE

# Checks for programs.
AC_PROG_INSTALL
AC_PROG_MAKE_SET

# Checks for libraries.

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.

# Internationalization support.
IT_PROG_INTLTOOL([0.35.0])

GETTEXT_PACKAGE=moblin-image-creator
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], ["$GETTEXT_PACKAGE"],
                   [The domain to use with gettext])
#AM_PATH_PYTHON([2.5.2])
AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_VERSION([0.16.1])

PROGRAMNAME_LOCALEDIR=[${datadir}/locale]
AC_SUBST(PROGRAMNAME_LOCALEDIR)

AC_CONFIG_FILES([Makefile po/Makefile.in
                 default_config/Makefile
                 gui/Makefile
                 help/Makefile
                 libs/Makefile
                 utils/Makefile
                 platforms/Makefile
                 platforms/mccaslin-lpia-fedora/Makefile
                 platforms/mccaslin-lpia-ubuntu-hardy-ppa-snapshot/Makefile
                 platforms/mccaslin-lpia-ubuntu-hardy-ppa/Makefile
                 platforms/mccaslin-lpia-ubuntu-hardy/Makefile
                 platforms/mccaslin-lpia/Makefile
                 platforms/menlow-lpia-ubuntu-hardy-jax10-snapshot1/Makefile
                 platforms/menlow-lpia-ubuntu-hardy-ppa-snapshot/Makefile
                 platforms/menlow-lpia-ubuntu-hardy-ppa/Makefile
                 platforms/menlow-lpia-ubuntu-hardy/Makefile
                 platforms/menlow-lpia/Makefile])
AC_OUTPUT
