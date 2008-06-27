########################################################################

AC_PREREQ(2.61)
AC_INIT([ndims branch builder],
	[m4_esyscmd([./build-helpers/package-version . version-stamp])],
	[hun@n-dimensional.de],
	[nbb])
AC_CONFIG_AUX_DIR([auto-aux])
AC_CONFIG_SRCDIR([src/nbb.in])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_TESTDIR([test])
AM_INIT_AUTOMAKE([-Wall -Werror foreign 1.10 dist-bzip2
                  readme-alpha std-options])

########################################################################

AC_PROG_SED
AC_PROG_GREP
AC_PROG_INSTALL

########################################################################

AM_PATH_PYTHON([2.4], [:],
               [AC_MSG_ERROR([nbb does require Python >= 2.4])])
AM_CONDITIONAL([HAVE_PYTHON], [ test "x$PYTHON" != "x:" ])

AC_ARG_VAR([PYDOC], [pydoc python documentation tool])
AC_PATH_PROG([PYDOC], [pydoc], [no])
AM_CONDITIONAL([HAVE_PYDOC], [test "x$PYDOC" != "xno"])

########################################################################

m4_pattern_forbid([NDIM_REQUIRE_POSIX_SH])dnl
NDIM_REQUIRE_POSIX_SH()dnl
m4_pattern_forbid([NDIM_DETECT_MAN2TXT])dnl
NDIM_DETECT_MAN2TXT()dnl

########################################################################

AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([GNUmakefile])
AC_CONFIG_FILES([src/nbblib/package.py:src/nbblib/package.in])
AC_CONFIG_FILES([test/atlocal])
AC_CONFIG_FILES([test/Makefile])
AC_OUTPUT

########################################################################
