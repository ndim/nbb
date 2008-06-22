########################################################################

AC_PREREQ(2.61)
AC_INIT([ndims branch builder],
	[m4_esyscmd([./build-helpers/package-version . version-stamp])],
	[hun@n-dimensional.de],
	[nbb])
AC_CONFIG_AUX_DIR([auto-aux])
AC_CONFIG_SRCDIR([nbb/nbb.in])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_TESTDIR([test])
AM_INIT_AUTOMAKE([-Wall -Werror foreign 1.10 dist-bzip2
                  readme-alpha std-options])

########################################################################

AC_PROG_SED

########################################################################

AM_PATH_PYTHON([2.4], [:], [:])
AM_CONDITIONAL([HAVE_PYTHON], [ test "x$PYTHON" != "x:" ])

########################################################################

m4_pattern_forbid([NDIM_REQUIRE_POSIX_SH])dnl
NDIM_REQUIRE_POSIX_SH()dnl
m4_pattern_forbid([NDIM_DETECT_MAN2TXT])dnl
NDIM_DETECT_MAN2TXT()dnl

########################################################################

AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([GNUmakefile])
AC_CONFIG_FILES([nbb/nbblib/package.py:nbb/nbblib/package.in])
AC_CONFIG_FILES([test/atlocal])
AC_CONFIG_FILES([test/Makefile])
AC_OUTPUT

########################################################################
