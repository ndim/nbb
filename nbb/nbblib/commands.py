import os

from nbblib.package import *
from nbblib.plugins import *
from nbblib.progutils import *
from nbblib.vcs import *
from nbblib.bs import *


def adjust_doc(doc):
    """Remove common whitespace at beginning of doc string lines"""
    if not doc: return doc
    i = 0
    for i in range(len(doc)):
        if doc[i] not in " \t":
            break
    prefix = doc[:i]
    rest_doc = doc[i:]
    almost_doc = rest_doc.replace("\n%s" % prefix, "\n")
    i = -1
    while almost_doc[i] == '\n':
        i = i - 1
    return almost_doc[:i]


class CommandLineError(Exception):
    def __init__(self, message, *args):
        super(CommandLineError, self).__init__()
        if args:
            self.msg = message % args
        else:
            self.msg = message
    def __str__(self):
        return "Command line error: %s" % self.msg


########################################################################
# Command plugin system
########################################################################

class Command(object):
    """
    Mount point for plugins which refer to commands that can be performed.

    Plugins implementing this reference should provide the following
    interface:

    name  attribute
        The text to be displayed, describing the version control system
    summary attribute
        Short (less than 50 chars) command summary line
    usage attribute
        Usage string (defaults to '')

    validate_args(*args, **kwargs)  function
        Must raise CommandLineError() if it encounters invalid arguments in cmdargs
    run() function
        Actually run the function

    FFF(*args, **kwargs)
        *args are the arguments from the command line
        **kwargs are additional parameters from within the program
    """
    __metaclass__ = GenericPluginMeta

    usage = ''

    def __init__(self, *args, **kwargs):
        self.validate_args(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        self.context = kwargs['context']

    def run(self):
        """Run the command"""
        raise NotImplementedError()

    def validate_args(self, *args, **kwargs):
        """Validate command line arguments"""
        print "Command: ", self.name
        print "*args:   ", args
        print "**kwargs:", kwargs
	if len(args) > 0:
            raise CommandLineError("'%s' command takes no parameters", self.name)

    def __str__(self):
        return "Command(%s, %s)" % (self.cmd_name, self.cmdargs)


class HelpCommand(Command):
    """\
    If the optional <command> is given, print the help for <command>.
    Else, print a list of commands and general help.
    """

    name = 'help'
    summary = 'print help text'
    usage = '[<command>]'

    def validate_args(self, *args, **kwargs):
        if len(args) == 1 and args[0] not in Command.plugins.keys():
            raise CommandLineError("'%s' is an invalid command name", args[0])
        elif len(args) > 1:
            raise CommandLineError("'%s' command only takes one optional parameter", self.name)

    def _print_command_list(self):
        print "List of commands:"
        keys = Command.plugins.keys()
        keys.sort()
        for k in keys:
           print "\t%-15s\t%s" % (k, Command.plugins[k].summary)

    def _print_command_help(self, cmd):
        """print help for command cmd"""
        c = Command.plugins[cmd]
        print "Purpose:", c.summary
        if c.usage:
            print "Usage:  ", self.context.prog, cmd, c.usage
        else:
            print "Usage:  ", self.context.prog, cmd
        if hasattr(c, '__doc__'):
            if c.__doc__:
                print
                print adjust_doc(c.__doc__)

    def run(self):
        if len(self.args) == 0:
            self._print_command_list()
        elif len(self.args) == 1:
            self._print_command_help(self.args[0])
        else:
            assert(False)


class InternalConfigCommand(Command):
    name = 'internal-config'
    summary = 'print internal program configuration'
    def run(self):
        print "Source tree types:",  ", ".join(VCSourceTree.plugins.keys())
        print "Build system types:", ", ".join(BSSourceTree.plugins.keys())
        print "Commands:",           ", ".join(Command.plugins.keys())


class SourceClassCommand(Command):
    """Base class for commands acting on source trees"""
    def __init__(self, *args, **kwargs):
        super(SourceClassCommand, self).__init__(*args, **kwargs)
        context = kwargs['context']
        srcdir = os.getcwd()
        absdir = os.path.abspath(srcdir)
        self.vcs_sourcetree = VCSourceTree.detect(absdir, context)
        if context.verbose:
            print "vcs_sourcetree", str(self.vcs_sourcetree)
        assert(self.vcs_sourcetree)
        cfg = self.vcs_sourcetree.config
        self.bs_sourcetree = BSSourceTree.detect(self.vcs_sourcetree, context)
        if context.verbose:
            print "bs_sourcetree", str(self.bs_sourcetree)
            print "CONFIG", cfg
            print " ", "srcdir", cfg.srcdir
            print " ", "builddir", cfg.builddir
            print " ", "installdir", cfg.installdir


class BuildTestCommand(SourceClassCommand):
    name = 'build-test'
    summary = 'simple build test'
    def run(self):
        self.bs_sourcetree.init()
        self.bs_sourcetree.configure()
        self.bs_sourcetree.build()
        self.bs_sourcetree.install()


class ConfigCommand(SourceClassCommand):
    name = 'config'
    summary = 'set/get config values'
    usage = '(srcdir|builddir|installdir)'

    def validate_args(self, *args, **kwargs):
        items = ('srcdir', 'builddir', 'installdir', )
        if len(args) == 0:
            raise CommandLineError("'%s' requires at least one parameter (%s)", self.name,
                                   ', '.join(items))
        elif len(args) == 1 and args[0] in items:
            pass
        elif len(args) == 2 and args[0] in items:
            if args[0] in ('srcdir', ):
                raise CommandLineError("'%s' command cannot change 'srcdir'", self.name)
            else:
                pass
        else:
            raise CommandLineError("'%s' requires less or different parameters", self.name)

    def run(self):
        git_get_items = ('builddir', 'installdir', 'srcdir')
        git_set_items = ('builddir', 'installdir', )
        if len(self.args) == 1:
            if self.args[0] in git_get_items:
                print getattr(self.vcs_sourcetree.config, self.args[0])
            else:
                assert(False)
        elif len(self.args) == 2:
            if self.args[0] == 'builddir':
                self.vcs_sourcetree.config.builddir = self.args[1]
            elif self.args[0] == 'installdir':
                self.vcs_sourcetree.config.installdir = self.args[1]
            else:
                assert(False)
        else:
            assert(False)


########################################################################
# Commands
########################################################################

class NBB_Command(object):
    def __init__(self, cmd, cmdargs, context):
        if Command.plugins.has_key(cmd):
            try:
                c = Command.plugins[cmd](*cmdargs, **{'context':context})
                c.run()
            except CommandLineError, e:
                print "%(prog)s: Fatal:" % context, e
                sys.exit(2)
            except ProgramRunError, e:
                print "%(prog)s: Fatal:" % context, e
                print "Program aborted."
        else:
            print "Fatal: Unknown command '%s'" % cmd
	    raise NotImplementedError()
        return

