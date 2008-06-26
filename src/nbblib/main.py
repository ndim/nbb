########################################################################
# Main program
########################################################################


"""\
nbb (ndim's branch builder) %(PACKAGE_VERSION)s
Build, install given branch of source code into a branch specific place
Copyright (C) 2007, 2008 Hans Ulrich Niedermann <hun@n-dimensional.de>
TBA: License conditions

Usage: %(prog)s [general options] <command> [command specific options]

Features:
 * supports git branches
 * supports bzr branches (requires useful branch nick, TBD: bzr config ?)
 * does out-of-source-tree builds (in-source-tree-builds unsupported)
 * direct support for automake/autoconf based build systems
 * TBD: supports execution of user commands in source, build, install dirs

DONE:
 * VCS config support ('git config', etc.)
 * Build system support: automake/autoconf
 * Merge stuff from Eclipse to src/own/nbb and vice versa.
 * Write test cases for init, configure, build, install.
 * Write test cases for all nbb commands.
 * Determine required feature sets (properties, new-style classes, etc.)
   and then check that the Python environment is actually compatible.
   @classmethod -> Python 2.4
   new style classes -> Python 2.2

TODO: (to get git-amb equivalent functionality)
 * Fine-tune init, configure, build, install commands with knowledge
   gained with git-amb, especially the command interdependencies.
 * Implement *-sh and *-run commands.

TODO: (Large list)
 * BS support: cmake, scons, ...
 * VCS support: SVN, darcs, hg, ...
 * Out-of-source builds for systems which require in-source-tree builds:
   "cp -rl foo.src foo.build"?
 * General removal of redundancy in Python code.
 * Make sure the if cmp ... mv .. rm in make rules are correct and useful.
 * More declarative syntax elements in the Python code.
 * Use declarations for command line parsing, and help text generation.
   Use optparse stuff for both global params and extra optparse stuff
   for each command?
 * Add pydoc docs.
 * Add global --nick or similar option to determine the branch
   name to use for composing the pathes.
 * Find or implement @abstractmethod decorator.
 * Test cases for proper handling of detecting (0, 1, >1) x (VCS, BS).
 * Unify detect() methods.
 * Store config in ${srcdir}/.nbb.conf instead of 'git config'?
   More portable. bzr does not have a config interface, for example.
 * Model different "stages" of e.g. automake builds as distinct objects,
   including proper dependency detectors, and stuff? OK, we're not going
   to duplicate scons here.
 * BS autodetection might discover more than one BS instance of the same type?
 * Design nice user interface. Requirements:
   * print top_srcdir, builddir, installdir. OK: 'config'
   * start subshell in top_srcdir, builddir, installdir
   * run 'autoreconf' type step. OK: 'init'
   * run 'configure' type step. OK: 'configure'
   * run 'make' type step. OK: 'build'
   * run 'make install' type step. OK: 'install'
   * run custom (make) commands. OK: 'make'
 * Bash syntax completion for that user interface.
 * Man page or something similar. Generate from help texts?

TBD: Command line interface:

  Run default build commands:
    $ %(prog)s [general options] init [command specific options]
    $ %(prog)s [general options] configure [command specific options]
    $ %(prog)s [general options] build [command specific options]
    $ %(prog)s [general options] install [command specific options]

  Run cleanup commands:
    $ %(prog)s [general options] purge [command specific options]
      Command specific options:
        --builddir-only
        --installdir-only
    $ %(prog)s [general options] purge-all    # either this
    $ %(prog)s [general options] purge --all  # or that
    TBD: 'make clean', 'make distclean' and similar stuff?

  Get/set config:
    $ %(prog)s [general options] config srcdir
    $ %(prog)s [general options] config builddir [<builddir>]
    $ %(prog)s [general options] config installdir [<installdir>]

  Start an interactive shell in either of the three directories:
    $ %(prog)s [general options] src-sh [command specific options]
    $ %(prog)s [general options] build-sh [command specific options]
    $ %(prog)s [general options] install-sh [command specific options]

  Run command in builddir:
    $ %(prog)s [general options] run <command> [<param>...]
    $ %(prog)s [general options] run [command specific options... <-->] <cmd>...

  (Not sure about these)
  Run a non-interactive shell command in either of the three directories:
    $ %(prog)s [general options] src-sh [command specific options] <command>...
    $ %(prog)s [general options] build-sh [command specific options] <command>...
    $ %(prog)s [general options] install-sh [command specific options] <cmd...>

Global options:

  -h --help          Print this help text
  -V --version       Print program version number

  -n --dry-run       Do not actually execute any commands

  -b --build-system  Force buildsystem detection (%(buildsystems)s)
  -v --vcs           Force VCS detection (%(vcssystems)s)
"""


import sys
import logging


from nbblib import bs
from nbblib import commands
from nbblib import package
from nbblib import plugins
from nbblib import vcs


def print_version(context):
    print "%(prog)s (ndim's branch builder) %(PACKAGE_VERSION)s" % context


def print_help(context):
    print __doc__ % context,


class PropertySetAgainError(Exception):
    def __str__(self):
        return "Property cannot be set more than once"


class InvalidPropertyValue(Exception):
    def __init__(self, value):
        super(InvalidPropertyValue, self).__init__()
        self.value = value
    def __str__(self):
        return "Property cannot be set to invalid value '%s'" % self.value


class Property(object):
    def __init__(self, **kwargs):
        if kwargs.has_key('default'):
            self.default = kwargs['default']
    def __get__(self, instance, owner):
        # print "Property.__get__", instance, owner
        if hasattr(self, 'value'):
            return self.value
        elif hasattr(self, 'default'):
            return self.default
        else:
            return None
    def __set__(self, instance, value):
        # print "Property.__set__", instance, value
        if hasattr(self, 'value'):
            raise PropertySetAgainError()
        elif not self.isvalid(value):
            raise InvalidPropertyValue
        else:
            self.value = self.convert(value)
    def __str__(self):
        if hasattr(self, 'value'):
            return self.value
        else:
            return '<undefined property>'
    def isvalid(self, value):
        return True
    def convert(self, value):
        return value


class ProgProperty(Property):
    def convert(self, value):
        prog = value
        idx = prog.rfind('/')
        if idx >= 0:
            prog = prog[idx+1:]
        return prog


class VCSProperty(Property):
    def isvalid(self, value):
        return (value in vcs.VCSourceTree.plugins.keys())


class BSProperty(Property):
    def isvalid(self, value):
        return (value in bs.BSSourceTree.plugins.keys())


class BoolProperty(Property):
    def __init__(self, default=False):
        super(BoolProperty, self).__init__(default=default)
    def isvalid(self, value):
        return (value in (True, False))

class DryRunProperty(BoolProperty):
    def __init__(self):
        super(DryRunProperty, self).__init__(default=False)


class Context(object):
    PACKAGE_VERSION = Property()
    prog = ProgProperty()
    vcs = VCSProperty()
    bs = BSProperty()
    dry_run = DryRunProperty()
    verbose = BoolProperty()
    vcssystems = Property()
    buildsystems = Property()

    def __getitem__(self, key):
        """emulate a dict() for the purpose of "%(prog)s" % context"""
        return getattr(self, key)


def main(argv):
    context = Context()
    context.PACKAGE_VERSION = package.PACKAGE_VERSION
    context.vcssystems = ", ".join(vcs.VCSourceTree.plugins.keys())
    context.buildsystems = ", ".join(bs.BSSourceTree.plugins.keys())
    context.prog = argv[0]

    if len(argv) < 2:
        raise commands.CommandLineError(\
            "%(prog)s requires some arguments",
            prog=context.prog)

    i = 1
    while i<len(argv):
        if argv[i][0] != '-':
            break
        if argv[i] in ('-h', '--help'):
            print_help(context)
            return
        elif argv[i] in ('-V', '--version'):
            print_version(context)
            return
        elif argv[i] in ('-n', '--dry-run'):
            context.dry_run = True
        elif argv[i] in ('-b', '--build-system'):
            i = i + 1
            assert(i<len(argv))
            context.bs = argv[i]
        elif argv[i][:6] == '--build-system=':
            context.bs = argv[i][6:]
        elif argv[i] in ('-v', '--vcs'):
            i = i + 1
            assert(i<len(argv))
            context.vcs = argv[i]
        elif argv[i][:6] == '--vcs=':
            context.vcs = argv[i][6:]
        elif argv[i] in ('--verbose', ):
            context.verbose = True
        # print "", i, argv[i]
        i = i + 1
    cmd = argv[i]
    cmdargs = argv[i+1:]
    nbb = commands.NBB_Command(cmd, cmdargs, context=context)


def cmdmain(argv):
    try:
        main(argv)
        logging.shutdown()
    except plugins.PluginNoMatch, e:
        logging.shutdown()
        print e
        sys.exit(1)
    except plugins.AmbigousPluginDetection, e:
        logging.shutdown()
        print e
        sys.exit(1)
    except commands.CommandLineError, e:
        logging.shutdown()
        print e
        sys.exit(2)
