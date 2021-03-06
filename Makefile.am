pkgpythondir = ${pythondir}/${PACKAGE_TARNAME}-${PACKAGE_VERSION_MAJOR}.${PACKAGE_VERSION_MINOR}
nbblibdir = ${pkgpythondir}/nbblib

ALL_LOCAL =

CLEANFILES =
BUILT_SOURCES =
EXTRA_DIST =
UPLOAD_FILES =
TESTS =

man1_MANS =
doc_DATA =
dist_doc_DATA =
bin_PROGRAMS =
check_PROGRAMS =
bin_SCRIPTS =
check_SCRIPTS =
python_PYTHON =
nodist_python_PYTHON =
nodist_nbblib_PYTHON =
nbblib_PYTHON =
AM_INSTALLCHECK_STD_OPTIONS_EXEMPT =

# For the test cases
export top_srcdir

AM_CPPFLAGS = -I${top_builddir}/include

ACLOCAL_AMFLAGS = -I m4 --install

SUBDIRS = . test

include build-helpers/package-version.mk

include Makefile-files
include src/Makefile-files

all-local: $(ALL_LOCAL)

if HAVE_NDIM_MAN2TXT
.man.txt:
	$(NDIM_MAN2TXT) "$<" > "$@.new"
	test -s "$@.new"
	mv -f "$@.new" "$@"
endif

# Requires git 1.5 to work properly.
if HAVE_GIT
# Usage: $ make tag VER=1.2
tag:
	test -d "$(top_srcdir)/.git"
	@cd "$(top_srcdir)" && $(GIT) status;:
	@cd "$(top_srcdir)" && if $(GIT) diff-files --quiet; then :; else \
		echo "Uncommitted local changes detected."; \
		exit 1; fi
	@cd "$(top_srcdir)" && if $(GIT) diff-index --cached --quiet HEAD; then :; else \
		echo "Uncommitted cached changes detected."; \
		exit 2; fi
	@if test "x$(VER)" = "x"; then \
		echo "VER not defined. Try 'make tag VER=2.11' or something similar."; \
		exit 3; \
        fi
	@test "x$$(echo "$(VER)" | $(SED) 's/^[0-9]\{1,\}\.[0-9]\{1,\}//')" = "x" || { \
		echo "VER=$(VER) is not in numerical 'x.y' format."; \
		exit 4; }
	@test "x$$($(SED) '1q' '$(top_srcdir)/NEWS')" = "x$(PACKAGE_TARNAME) $(VER)" || { \
		echo "NEWS does not start with entry for '$(PACKAGE_TARNAME) $(VER)'"; \
		exit 5; }
	@$(SED) -n '1p; 2,/^$(PACKAGE_TARNAME) / p' '$(top_srcdir)/NEWS' \
		| $(SED) '$$ { /^$(PACKAGE_TARNAME) / d }' | $(SED) '$$ { /^$$/d }' \
		> TAG-MESSAGE
	@echo "======================================================================="
	@cat TAG-MESSAGE
	@echo "======================================================================="
	@echo "Do you really want to tag this as release '$(PACKAGE_TARNAME)-$(VER)'? Enter to continue, Ctrl-C to abort."
	@read
	msgfile="$$PWD/TAG-MESSAGE"; \
	cd "$(top_srcdir)" && $(GIT) tag -s -F "$$msgfile" "$(PACKAGE_TARNAME)-$(VER)"; \
	rm -f "$$msgfile"
endif

if HAVE_RSYNC
UPLOAD_DIR = upload-dir
ALL_UPLOAD_FILES = $(UPLOAD_FILES) $(distdir).tar.bz2
upload: $(UPLOAD_FILES) dist
	rm -rf "$(UPLOAD_DIR)"
	mkdir -p "$(UPLOAD_DIR)"
	for f in $(ALL_UPLOAD_FILES); do \
		ln "$$(test -e "$$f" || echo "$(top_srcdir)/")$$f" "$(UPLOAD_DIR)/"; \
	done
	rsync -avz --delete "$(UPLOAD_DIR)/" $(RSYNC_HOST):$(RSYNC_DIR)/$(PACKAGE_TARNAME)/
	rm -rf "$(UPLOAD_DIR)"
	if test -d "$(top_srcdir)/.git"; then cd "$(top_srcdir)" && git push public master; fi
endif

clean-local:
	rm -rf "$(UPLOAD_DIR)"

# End of Makefile.am.
