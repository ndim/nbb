"""\
nbblib.commands - generic cmdline command infrastructure
Copyright (C) 2008 Hans Ulrich Niedermann <hun@n-dimensional.de>
"""

import logging


import nbblib.plugins as plugins


__all__ = []


__all__.append('CommandLineError')
class CommandLineError(Exception):
    def __init__(self, message):
        super(CommandLineError, self).__init__()
        self.msg = message
    def __str__(self):
        return "Command line error: %s" % self.msg


__all__.append('UnknownCommand')
class UnknownCommand(Exception):
    def __init__(self, context, cmd):
        super(UnknownCommand, self).__init__()
        self.prog = context.prog
        self.cmd = cmd
    def __str__(self):
        return "Unknown %(prog)s command '%(cmd)s'" % self.__dict__


########################################################################
# Command plugin system
########################################################################


__all__.append('Command')
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
    __metaclass__ = plugins.GenericPluginMeta

    usage = ''

    def __init__(self, context, *args, **kwargs):
        super(Command, self).__init__()
        self.validate_args(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        self.context = context

    @plugins.abstractmethod
    def run(self):
        """Run the command"""
        pass

    @plugins.abstractmethod
    def validate_args(self, *cmdargs, **kwargs):
        """Validate command line arguments: Abstract method.

        May make use of self.context.
        """
        pass

    def validate_args_none(self, *cmdargs, **kwargs):
        """Validate command line arguments: no argument at all"""
        logging.debug("Command:  %s", self.name)
        logging.debug("*cmdargs: %s", cmdargs)
        logging.debug("**kwargs: %s", kwargs)
        if len(cmdargs) > 0:
            raise CommandLineError("'%s' command takes no parameters"
                                   % self.name)
        logging.debug("Command match!")
        return True

    def validate_args_any(self, *cmdargs, **kwargs):
        """Validate command line arguments: accept any argument"""
        logging.debug("Command:  %s", self.name)
        logging.debug("*cmdargs: %s", cmdargs)
        logging.debug("**kwargs: %s", kwargs)
        logging.debug("Command match!")
        return True

    def __str__(self):
        return "Command(%s, %s)" % (self.cmd_name, self.cmdargs)


__all__.append('Commander')
class Commander(object):

    def __init__(self, context, cmd, *cmdargs):
        self.context = context
        logging.debug("Commander() %s %s", cmd, cmdargs)
        if cmd in Command.plugins:
            self.command = Command.plugins[cmd](context, *cmdargs)
        else:
            raise UnknownCommand(context, cmd)

    def run(self):
        self.command.run()

