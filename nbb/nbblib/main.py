########################################################################
# Main program
########################################################################


"""\
nbb (ndim's branch builder) %(PACKAGE_VERSION)s
Build, install given branch of source code into a branch specific place
Copyright (C) 2007, 2008 Hans Ulrich Niedermann <hun@n-dimensional.de>
TBA: License conditions

Usage: %(prog)s <to-be-determined>

Features:
 * supports git branches
 * supports bzr branches (requires useful branch nick, TBD: bzr config ?)
 * does out-of-source-tree builds (in-source-tree-builds unsupported)
 * direct support for automake/autoconf based build systems
 * TBD: supports execution of user commands in source, build, install dirs

DONE:
 * VCS config support ('git config', etc.)
 * Build system support: automake/autoconf

TODO: (Large list)
 * Build system support: cmake, scons, ...
 * Fine-tune init, configure, build, install commands with knowledge
   gained with git-amb, especially the command interdependencies.
 * implement *-sh and *-run commands
 * General removal of redundancy in Python code.
 * More declarative syntax elements in the Python code.
 * Use declarations for command line parsing, and help text generation.
 * Add global --nick or similar option to determine the branch
   name to use for composing the pathes.
 * Store config in ${srcdir}/.nbb.conf instead of 'git config'?
   More portable. bzr does not have a config interface, for example.
 * Model different "stages" of e.g. automake builds as distinct objects,
   including proper dependency detectors, and stuff? OK, we're not going
   to duplicate scons here.
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


from nbblib.bs import *
from nbblib.commands import *
from nbblib.package import *
from nbblib.vcs import *


def print_version(context):
    print "%(prog)s (ndim's branch builder) %(PACKAGE_VERSION)s" % context


def print_help(context):
    print __doc__ % context,


class Property(object):
    def __init__(self, **kwargs):
        if kwargs.has_key('default'):
            self.default = kwargs['default']
    def __get__(self, instance, owner):
        if hasattr(self, 'value'):
            return self.value
        elif hasattr(self, 'default'):
            return self.default
        else:
            return None
    def __set__(self, instance, value):
        if hasattr(self, 'value'):
            raise "Property cannot be set more than once"
        elif not self.isvalid(value):
            raise "Property cannot be set to invalid value '%s'" % value
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
        return (value in VCSourceTree.plugins.keys())


class BSProperty(Property):
    def isvalid(self, value):
        return (value in BSSourceTree.plugins.keys())


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
    context.PACKAGE_VERSION = PACKAGE_VERSION
    context.vcssystems = ", ".join(VCSourceTree.plugins.keys())
    context.buildsystems = ", ".join(BSSourceTree.plugins.keys())
    context.prog = argv[0]

    if len(argv) < 2:
        print "Fatal: %(prog)s requires some arguments" % context
        return 2

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
    nbb = NBB_Command(cmd, cmdargs, context=context)
