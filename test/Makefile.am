# tests/Makefile.am - handle the autotest based testsuite

EXTRA_DIST =
DISTCLEANFILES =

TESTCASES =
TESTCASES += autotest.at
TESTCASES += nbb-basic.at
TESTCASES += nbb-detect.at
TESTCASES += nbb-config.at
TESTCASES += nbb-scons.at
TESTCASES += nbb-automake.at
TESTCASES += nbb-runsh.at
# Add more testcases here

EXTRA_DIST += $(TESTCASES)

TESTSUITE_NAME = nbb-foo
TESTSUITE_COPYRIGHT = Copyright (C) 2007, 2008 Hans Ulrich Niedermann
TESTED_EXECUTABLES = git bzr
TESTSUITE = testsuite

EXTRA_DIST += atlocal.in local.at
DISTCLEANFILES += atconfig atlocal

DISTCLEANFILES += \
	testsuite.log \
	testsuite.dir/at-stderr \
	testsuite.dir/at-stdout \
	testsuite.dir/at-check-line \
	testsuite.dir/at-status

git-version-check:
	cd $(top_builddir) && $(MAKE) git-version-check

check-local: git-version-check atconfig atlocal $(srcdir)/$(TESTSUITE)
	@echo "INFO: Running uninstalled test suite"; \
	abs_top_builddir="$$(cd "$(top_builddir)" > /dev/null 2>&1 && pwd)"; \
	abs_top_srcdir="$$(cd "$(top_srcdir)" > /dev/null 2>&1 && pwd)"; \
	echo "     " $(SHELL) "$(srcdir)/$(TESTSUITE)" AUTOTEST_PATH=`cd $(top_builddir)/src > /dev/null && pwd` PYTHONPATH="$${abs_top_builddir}/src" PYTHON="$(PYTHON)" NBB_SCRIPT="$${abs_top_builddir}/src/nbb" $(TESTSUITEFLAGS); \
	$(SHELL) "$(srcdir)/$(TESTSUITE)" AUTOTEST_PATH=`cd $(top_builddir)/src > /dev/null && pwd` \
		PYTHONPATH="$${abs_top_builddir}/src" \
		PYTHON="$(PYTHON)" \
		NBB_SCRIPT="$${abs_top_builddir}/src/nbb" \
		$(TESTSUITEFLAGS)

installcheck-local: atconfig atlocal $(srcdir)/$(TESTSUITE)
	@echo "INFO: Running installed test suite"; \
	$(SHELL) "$(srcdir)/$(TESTSUITE)" AUTOTEST_PATH='$(DESTDIR)$(bindir)' \
		PYTHONPATH="$(DESTDIR)$(pythondir)" \
		PYTHON="$(PYTHON)" \
		NBB_SCRIPT="$(DESTDIR)$(bindir)/nbb" \
		$(TESTSUITEFLAGS)

clean-local:
	test ! -f '$(srcdir)/$(TESTSUITE)' || \
		$(SHELL) '$(srcdir)/$(TESTSUITE)' --clean

# Note about the location of testsuite.at, $(TESTSUITE), and package.m4:
# We locate these files in the $(srcdir), because
#  a) They are shipped in the source tarball.
#  b) If they are created in $(builddir), they will need to be removed on
#     "make clean" or "make distclean". Re-generation requires tools a
#     normal system does not need to have.
#  c) They do not change depending on any configure run, they only change
#     depending on configure.ac or tests/Makefile.am updates - and those
#     require special build tools to handle anyway. Thus, a normal build
#     will not touch these files at all and just leave the filese from
#     upstream in place.

# testsuite.at depends on Makefile.in to make sure that changes in the
# list of TESTCASES are reflected in testsuite.at. We do not depend on
# Makefile, as Makefile is re-created on every ./configure run, and that
# does not imply an addition to TESTCASES.
EXTRA_DIST += $(srcdir)/testsuite.at
$(srcdir)/testsuite.at: $(TESTCASES) Makefile.in
	@:; echo "INFO: Checking $(srcdir)/testsuite.at is up to date"; \
	{ \
		echo "dnl testsuite.at autogenerated from tests/Makefile.am"; \
		echo "AT_INIT()"; : "([$(TESTSUITE_NAME)])"; \
		echo "AT_COPYRIGHT([$(TESTSUITE_COPYRIGHT)])"; \
		for exe in $(TESTED_EXECUTABLES); do \
			echo "AT_TESTED([$${exe}])"; \
		done; \
		for tc in $(TESTCASES); do \
			echo "m4_include([$${tc}])"; \
		done; \
	} > testsuite.at.new
	@if test -f $(srcdir)/testsuite.at \
	 && cmp testsuite.at.new $(srcdir)/testsuite.at > /dev/null; \
	then rm -f testsuite.at.new; \
	else echo "INFO: Updating $(srcdir)/testsuite.at"; \
	     mv -f testsuite.at.new $(srcdir)/testsuite.at; fi

# FIXME: Hack to handle unset AUTOM4TE variable
EXTRA_DIST += $(srcdir)/$(TESTSUITE)
$(srcdir)/$(TESTSUITE): testsuite.at local.at package.m4 $(TESTCASES)
	@echo "INFO: Checking whether $(srcdir)/$(TESTSUITE) is up to date"; \
	AUTOM4TE="$(AUTOM4TE)"; \
	if test "x$${AUTOM4TE}" = "x"; then AUTOM4TE="autom4te"; fi; \
	$${AUTOM4TE} --language=autotest -I '$(srcdir)' -o $(TESTSUITE).tmp $(srcdir)/testsuite.at
	@if test -f $(srcdir)/$(TESTSUITE) && cmp $(TESTSUITE).tmp $(srcdir)/$(TESTSUITE) > /dev/null; \
	then rm -f $(TESTSUITE).tmp; \
	else echo "INFO: Updating $(srcdir)/$(TESTSUITE)"; \
	     mv -f $(TESTSUITE).tmp $(srcdir)/$(TESTSUITE); fi

EXTRA_DIST += $(srcdir)/package.m4
$(srcdir)/package.m4: $(top_srcdir)/configure.ac $(top_builddir)/config.status Makefile.in
	@:;  echo "INFO: Checking $(srcdir)/package.m4 is up to date"; \
	{ \
		echo '# Signature of the current package (generated by tests/Makefile.am).'; \
		echo 'm4_define([AT_PACKAGE_NAME],      [@PACKAGE_NAME@])'; \
		echo 'm4_define([AT_PACKAGE_TARNAME],   [@PACKAGE_TARNAME@])'; \
		echo 'm4_define([AT_PACKAGE_VERSION],   [@PACKAGE_VERSION@])'; \
		echo 'm4_define([AT_PACKAGE_STRING],    [@PACKAGE_STRING@])'; \
		echo 'm4_define([AT_PACKAGE_BUGREPORT], [@PACKAGE_BUGREPORT@])'; \
	} > package.m4.tmp
	@if test -f $(srcdir)/package.m4 && cmp package.m4.tmp $(srcdir)/package.m4; \
	then rm -f package.m4.tmp; \
	else echo "INFO: Updating $(srcdir)/package.m4"; \
	     mv -f package.m4.tmp $(srcdir)/package.m4; fi

dist-hook:
	$(MAKE) $(srcdir)/package.m4 $(srcdir)/$(TESTSUITE)

# End of tests/Makefile.am.

