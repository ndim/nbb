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

Command line interface (implemeted):

  Run default build commands:
    $ %(prog)s [general options] init [command specific options]
    $ %(prog)s [general options] configure [command specific options]
    $ %(prog)s [general options] build [command specific options]
    $ %(prog)s [general options] install [command specific options]

  Get/set config:
    $ %(prog)s [general options] config srcdir
    $ %(prog)s [general options] config builddir [<builddir>]
    $ %(prog)s [general options] config installdir [<installdir>]

  Start an interactive shell in either of the three directories:
    $ %(prog)s [general options] sh --srcdir [command specific options]
    $ %(prog)s [general options] sh [--builddir] [command specific options]
    $ %(prog)s [general options] sh --installdir [command specific options]

  Run command in either of the three directories:
    $ %(prog)s [general options] run --srcdir <command> [<param>...]
    $ %(prog)s [general options] run [--builddir] <command> [<param>...]
    $ %(prog)s [general options] run --installdir <command> [<param>...]

TBD: Command line interface:

  Run cleanup commands:
    $ %(prog)s [general options] purge [command specific options]
      Command specific options:
        --builddir-only
        --installdir-only
    $ %(prog)s [general options] purge-all    # either this
    $ %(prog)s [general options] purge --all  # or that
    TBD: 'make clean', 'make distclean' and similar stuff?

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
from nbblib import progutils


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
        if 'default' in kwargs:
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
    vcssystems = Property()
    buildsystems = Property()

    def __init__(self):
        super(Context, self).__init__()
        for k in dir(self):
            a = getattr(self, k)
            if isinstance(a, Property):
                logging.debug("setting property_name for %s", k)
                a.property_name = k

    def __getitem__(self, key):
        """emulate a dict() for the purpose of "%(prog)s" % context"""
        return getattr(self, key)

    def __str__(self):
        kk = [x for x in dir(self) if (x.find('__') < 0) and (x.find('--') < 0)]
        kk.sort()
        lll = ( (k, getattr(self,k)) for k in kk )
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(("%s=%s" % (a,repr(c))
                                      for a,c in lll)))


def main(argv):
    context = Context()
    context.PACKAGE_VERSION = package.PACKAGE_VERSION
    context.vcssystems = ", ".join(vcs.VCSourceTree.plugins.keys())
    context.buildsystems = ", ".join(bs.BSSourceTree.plugins.keys())
    context.prog = argv[0]

    if len(argv) < 2:
        raise commands.CommandLineError(\
            "%(prog)s requires some arguments" % context)

    i = 1
    while i<len(argv):
        if argv[i][0] != '-':
            break
        elif argv[i] in ('-h', '--help'):
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
        elif argv[i][:15] == '--build-system=':
            context.bs = argv[i][6:]
        elif argv[i] in ('-v', '--vcs'):
            i = i + 1
            assert(i<len(argv))
            context.vcs = argv[i]
        elif argv[i][:6] == '--vcs=':
            context.vcs = argv[i][6:]
        elif argv[i] in ('--info', '--debug'):
            pass # acted on in previous stage
        else:
            raise commands.CommandLineError(\
                'Unknown global option %s' % repr(argv[i]))
        i = i + 1

    logging.info("Context: %s", context)
    cmd = argv[i]
    cmdargs = argv[i+1:]

    cdr = commands.Commander(context, cmd, *cmdargs)
    cdr.run()


def cmdmain(argv):
    try:
        main(argv)
        logging.shutdown()
    except commands.CommandLineError, e:
        logging.error(e)
        logging.shutdown()
        sys.exit(2)
    except commands.UnknownCommand, e:
        logging.error(e)
        logging.shutdown()
        sys.exit(2)
    except plugins.PluginNoMatch, e:
        logging.error(e)
        logging.shutdown()
        sys.exit(1)
    except plugins.AmbigousPluginDetection, e:
        logging.error(e)
        logging.shutdown()
        sys.exit(1)
    except RuntimeError, e:
        logging.error(e)
        logging.shutdown()
        sys.exit(1)
    except progutils.ProgramRunError, e:
        logging.error(e)
        logging.shutdown()
        sys.exit(3)
    except SystemExit, e:
        logging.error("Someone called sys.exit() who should not have", exc_info=e)
        logging.shutdown()
        raise


__all__ = ['cmdmain', 'main']


