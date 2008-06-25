from nbblib.bs import *
from nbblib.commands import *
from nbblib.package import *
from nbblib.plugins import *
from nbblib.vcs import *
from nbblib.bs import *

for submodule in ('newplugins', ):
    setattr(__module__, submodule, __import__("nbblib.%s" % submodule))
