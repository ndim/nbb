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
    def __init__(self, *args, **kwargs):
        assert(len(args) == 0)
        if kwargs.has_key('default'):
            self.default = kwargs['default']
        valid_kwargs = ('default',)
        for kwa in kwargs.iterkeys():
            assert(kwa in valid_kwargs)
        self.name = "property-%08x" % hash(self)
    def __get__(self, instance, owner):
        # print "Property.__get__", instance, owner
        if hasattr(instance, self.name):
            return getattr(instance, self.name)
        elif hasattr(self, 'default'):
            return self.default
        else:
            return None
    def __set__(self, instance, value):
        # print "Property.__set__", instance, value
        if hasattr(instance, self.name):
            raise PropertySetAgainError()
        elif not self.isvalid(value):
            raise InvalidPropertyValue
        else:
            setattr(instance, self.name, self.convert(value))
    def __str__(self):
        if hasattr(instance, self.name):
            return getattr(instance, self.name)
        elif hasattr(self, 'default'):
            return '<property defaulting to %s>' % self.default
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
    except SystemExit, e:
        logging.shutdown()
        raise

