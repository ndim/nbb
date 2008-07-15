"""\
nbblib.nbbcommands - implementation of nbb commands
Copyright (C) 2008 Hans Ulrich Niedermann <hun@n-dimensional.de>
"""

import sys
import os
import logging


import nbblib.package as package
import nbblib.progutils as progutils
import nbblib.vcs as vcs
import nbblib.bs as bs
from nbblib.commands import *


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
            raise CommandLineError("'%s' is an invalid command name" % args[0])
        elif len(args) > 1:
            raise CommandLineError("'%s' command only takes one optional parameter" % self.name)

    def _print_command_list(self):
        print "List of commands:"
        keys = Command.plugins.keys()
        if not keys:
            raise Exception("No commands found. Please lart the developer.")
        keys.sort()
        keys2 = Command.plugins.keys()
	keys2.sort(lambda a,b: cmp(len(b),len(a)))
	print "keys ", keys
	print "keys2", keys2
        fmt = "\t%%-%ds\t%%s" % len(keys2[0])
        for k in keys:
           print fmt % (k, Command.plugins[k].summary)

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
    validate_args = Command.validate_args_none
    def run(self):
        print "Source tree types:",  ", ".join(vcs.VCSourceTree.plugins.keys())
        print "Build system types:", ", ".join(bs.BSSourceTree.plugins.keys())
        print "Commands:",           ", ".join(Command.plugins.keys())


class SourceClassCommand(Command):
    """Base class for commands acting on source trees"""
    name = None # abstract command class
    def __init__(self, context, *args, **kwargs):
        super(SourceClassCommand, self).__init__(context, *args, **kwargs)

        srcdir = os.getcwd()
        absdir = os.path.abspath(srcdir)

        self.vcs_sourcetree = vcs.VCSourceTree.detect(context, absdir)
        logging.debug("vcs_sourcetree %s", self.vcs_sourcetree)

        self.bs_sourcetree = bs.BSSourceTree.detect(context,
                                                    self.vcs_sourcetree)
        logging.debug("bs_sourcetree %s", self.bs_sourcetree)

        cfg = self.vcs_sourcetree.config
        for x in ('srcdir', 'builddir', 'installdir'):
            logging.info("CONFIG %s %s", x, getattr(cfg, x))


class DetectCommand(Command):
    name = None
    def __init__(self, context, *args, **kwargs):
        super(DetectCommand, self).__init__(context, *args, **kwargs)
        self.srcdir = os.getcwd()
        self.absdir = os.path.abspath(self.srcdir)
    validate_args = Command.validate_args_none


class DetectVCSCommand(DetectCommand):
    name = "detect-vcs"
    summary = "detect source tree VCS"
    def __init__(self, context, *args, **kwargs):
        super(DetectVCSCommand, self).__init__(context, *args, **kwargs)
        self.vcs_sourcetree = vcs.VCSourceTree.detect(self.context, self.absdir)
        logging.debug("vcs_sourcetree %s", self.vcs_sourcetree)
    def run(self):
        if self.vcs_sourcetree:
            print 'VCS:', self.vcs_sourcetree.name, self.vcs_sourcetree.tree_root
        else:
            print 'VCS:', 'Not detected'
    validate_args = Command.validate_args_none


class DetectBSCommand(DetectCommand):
    name = "detect-bs"
    summary = "detect source tree BS"
    def __init__(self, context, *args, **kwargs):
        super(DetectBSCommand, self).__init__(context, *args, **kwargs)
        self.vcs_sourcetree = vcs.VCSourceTree.detect(self.context, self.absdir)
        logging.debug("vcs_sourcetree %s", self.vcs_sourcetree)
        self.bs_sourcetree = bs.BSSourceTree.detect(self.context,
                                                    self.vcs_sourcetree)
        logging.debug("bs_sourcetree %s", self.bs_sourcetree)
    def run(self):
        if self.bs_sourcetree:
            print 'BS:', self.bs_sourcetree.name, self.bs_sourcetree.tree_root
        else:
            print 'BS:', 'Not detected'
    validate_args = Command.validate_args_none


class BuildTestCommand(SourceClassCommand):
    name = 'build-test'
    summary = 'simple build test'
    def run(self):
        self.bs_sourcetree.init()
        self.bs_sourcetree.configure()
        self.bs_sourcetree.build()
        self.bs_sourcetree.install()
    validate_args = Command.validate_args_none


class InitCommand(SourceClassCommand):
    name = 'init'
    summary = 'initialize buildsystem (e.g. "autoreconf")'
    validate_args = Command.validate_args_none
    def run(self):
        self.bs_sourcetree.init()


class ConfigureCommand(SourceClassCommand):
    name = 'configure'
    summary = 'configure buildsystem (e.g. "./configure")'
    validate_args = Command.validate_args_none
    def run(self):
        self.bs_sourcetree.configure()


class BuildCommand(SourceClassCommand):
    name = 'build'
    summary = 'build from source (e.g. "make")'
    validate_args = Command.validate_args_none
    def run(self):
        self.bs_sourcetree.build()


class InstallCommand(SourceClassCommand):
    name = 'install'
    summary = 'install the built things (e.g. "make install")'
    validate_args = Command.validate_args_none
    def run(self):
        self.bs_sourcetree.install()


class MakeCommand(SourceClassCommand):
    name = 'make'
    summary = 'run make in builddir'
    validate_args = Command.validate_args_any
    def run(self):
        os.chdir(self.bs_sourcetree.config.builddir)
        progutils.prog_run(["make"] + list(self.args),
                           self.context)


class GeneralRunCommand(SourceClassCommand):
    """Run general command in some branch specific dir

    """
    name = 'run'
    summary = 'run some command in branch specific dir'
    validate_args = Command.validate_args_any
    def __init__(self, context, *args, **kwargs):
        super(GeneralRunCommand, self).__init__(context, *args, **kwargs)
        self.rundir = None
        self.run_in = 'builddir'
        if len(self.args):
            if self.args[0] == '--srcdir':
                self.args = self.args[1:]
                self.rundir = self.bs_sourcetree.config.srcdir
                self.run_in = 'srcdir'
            elif self.args[0] == '--installdir':
                self.args = self.args[1:]
                self.rundir = self.bs_sourcetree.config.installdir
                self.run_in = 'installdir'
            elif self.args[0] == '--builddir':
                self.args = self.args[1:]
        if not self.rundir:
            self.rundir = self.bs_sourcetree.config.builddir
    def chdir(self):
        if os.path.exists(self.rundir):
            os.chdir(self.rundir)
        else:
            raise RuntimeError("The %s directory %s does not exist"
                               % (self.run_in, repr(self.rundir)))
    def run(self):
        self.chdir()
        progutils.prog_run(list(self.args), self.context)


class GeneralShellCommand(GeneralRunCommand):
    name    = 'sh'
    summary = 'run shell in branch specific dir'
    def get_shell_prompt(self):
        return r",--[Ctrl-d or 'exit' to quit this %s shell for branch '%s']--\n| <%s %s> %s\n\`--[\u@\h \W]\$ " \
            % (self.context.prog, self.vcs_sourcetree.branch_name,
               self.context.prog, self.name, self.get_run_in_dir(), )
    def run(self):
        self.chdir()
        # FIXME: Allow using $SHELL or similar.
        progutils.prog_run(['sh'] + list(self.args), self.context,
                           env_update = {'PS1': self.get_shell_prompt()})


class SrcShellCommand(GeneralShellCommand):
    name    = 'sh-src'
    summary = 'run interactive shell in source dir'
    run_in  = 'srcdir'


class BuildShellCommand(GeneralShellCommand):
    name    = 'sh-build'
    summary = 'run interactive shell in build dir'
    run_in  = 'builddir'


class InstallShellCommand(GeneralShellCommand):
    name    = 'sh-install'
    summary = 'run interactive shell in install dir'
    run_in  = 'installdir'


class ConfigCommand(SourceClassCommand):
    name = 'config'
    summary = 'set/get config values'
    usage = '(srcdir|builddir|installdir)'

    def validate_args(self, *args, **kwargs):
        items = ('srcdir', 'builddir', 'installdir', )
        if len(args) == 0:
            raise CommandLineError("'%s' command requires at least one parameter (%s)"
                                   % (self.name, ', '.join(items)))
        elif len(args) == 1 and args[0] in items:
            pass
        elif len(args) == 2 and args[0] in items:
            if args[0] in ('srcdir', ):
                raise CommandLineError("'%s' command cannot change 'srcdir'"
                                       % self.name)
            else:
                pass
        else:
            raise CommandLineError("'%s' requires less or different parameters"
                                   % self.name)

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


# End of file.

