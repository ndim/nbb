"""Convenience package for nbb

How exactly to cleanly import the modules in the future is still unclear,
so we'll just keep it as is for now.
"""

import nbblib.bs as bs
import nbblib.commands as commands
import nbblib.nbbcommands as nbbcommands
import nbblib.plugins as plugins
import nbblib.package as package
import nbblib.progutils as progutils
import nbblib.vcs as vcs

from nbblib.package import PACKAGE_VERSION

__all__ = ['bs', 'commands',
           'package', 'plugins',
           'progutils',
           'vcs',
           'PACKAGE_VERSION']
