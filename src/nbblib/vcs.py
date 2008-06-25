import os
import logging
import urlparse

from nbblib.package import *
from nbblib.plugins import *
from nbblib.progutils import *

from nbblib import newplugins


class AbstractConfig(object):
    """Return static config until we implement real config reading"""

    def __init__(self, srcdir, nick):
        super(AbstractConfig, self).__init__()
        self._srcdir = srcdir
        self._nick = nick

    def get_srcdir(self):
        return os.path.join(self._srcdir)
    srcdir = property(get_srcdir)

    def get_builddir(self):
        return os.path.join(self._srcdir, "_build", self._nick)
    builddir = property(get_builddir)

    def get_installdir(self):
        return os.path.join(self._srcdir, "_install", self._nick)
    installdir = property(get_installdir)


########################################################################
# VCS Source Tree plugin system
########################################################################

class NotAVCSourceTree(Exception):
    pass


class AmbigousVCSource(Exception):
    def __init__(self, srcdir, matches):
        super(AmbigousVCSource, self).__init__()
        self.srcdir = srcdir
        self.matches = matches
    def __str__(self):
        fmt = "  %-9s %-15s %s"
        def strmatch(m):
            return fmt % (m.name, m.branch_name(), m.tree_root())
        alist = ([fmt % ('VCS Type', 'Branch Name', 'Source tree root')] +
                 [fmt % (m.name, m.branch_name(), m.tree_root()) for m in self.matches])
        return ("More than one source tree VCS type detected for '%s':\n#%s"
                % (self.srcdir, '\n '.join(alist)))


class VCSourceTree(newplugins.GenericDetectPlugin):
    """
    Mount point for plugins which refer to actions that can be performed.

    Plugins implementing this reference should provide the following
    interface:

    name  attribute
        The text to be displayed, describing the version control system
    __init__  function
        Must raise NotAVCSourceTree() if it is not a VCS source tree
    """
    __metaclass__ = GenericPluginMeta
    no_match_exception = PluginNoMatch
    ambigous_match_exception = AmbigousPluginDetection

    @classmethod
    def validate(cls, obj, *args, **kwargs):
        srcdir = args[0]
        return obj.tree_root() == srcdir

    def get_config(self):
        """Get configuration object which determines builddir etc"""
        return AbstractConfig(self.tree_root(), self.branch_name())
    config = property(get_config)

    def tree_root(self):
        """Get absolute path to source tree root"""
        raise NotImplementedError()

    def branch_name(self):
        """Return name identifying the branch"""
        raise NotImplementedError()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<%s(%s, %s)>" % (self.__class__.__name__,
                                 repr(self.tree_root()),
                                 repr(self.branch_name()))


########################################################################
# VCS Source Tree plugins
########################################################################

class GitSourceTree(VCSourceTree):

    name = 'git'

    def __init__(self, context, srcdir):
        super(GitSourceTree, self).__init__(context)
        os.chdir(srcdir)
        if "true" != prog_stdout(["git", "rev-parse",
                                  "--is-inside-work-tree"]):
            raise NotAVCSourceTree()
        reldir = prog_stdout(["git", "rev-parse", "--show-cdup"])
        if reldir:
            os.chdir(reldir)
        self.__tree_root = os.getcwd()

    def get_config(self):
        return GitConfig(self.tree_root(), self.branch_name())
    config = property(get_config)

    def tree_root(self):
        return self.__tree_root

    def branch_name(self):
        bname = prog_stdout(["git", "symbolic-ref", "HEAD"])
        refs,heads,branch = bname.split('/')
        assert(refs=='refs' and heads=='heads')
        return branch


class GitConfig(AbstractConfig):
    """git config interface"""

    def __init__(self, *args, **kwargs):
        super(GitConfig, self).__init__(*args, **kwargs)

    def _itemname(self, item): return '.'.join((GIT_CONFIG_PREFIX, item, ))
    def _myreldir(self, rdir):
        return os.path.join(self._srcdir, rdir, self._nick)

    def get_builddir(self):
        ret, stdout, stderr = prog_retstd(['git', 'config', self._itemname('builddir')])
        assert(stderr == "")
	if ret == 0 and stdout:
            return self._myreldir(stdout)
        else:
            return super(GitConfig, self).get_builddir()

    def set_builddir(self, value):
        ret, stdout, stderr = prog_retstd(['git', 'config', self._itemname('builddir'), value])
        assert(ret == 0 and stdout == "" and stderr == "")

    builddir = property(get_builddir, set_builddir)

    def get_installdir(self):
        ret, stdout, stderr = prog_retstd(['git', 'config', self._itemname('installdir')])
        assert(stderr == "")
	if ret == 0 and stdout:
            return self._myreldir(stdout)
        else:
            return super(GitConfig, self).get_installdir()

    def set_installdir(self, value):
        ret, stdout, stderr = prog_retstd(['git', 'config', self._itemname('installdir'), value])
        assert(ret == 0 and stdout == "" and stderr == "")

    installdir = property(get_installdir, set_installdir)


class BzrSourceTree(VCSourceTree):

    name = 'bzr'

    def __init__(self, context, srcdir):
        super(BzrSourceTree, self).__init__(context)
        try:
            import bzrlib.workingtree
            wt,b = bzrlib.workingtree.WorkingTree.open_containing(srcdir)
        except bzrlib.errors.NotBranchError:
            raise NotAVCSourceTree()
        except ImportError:
            raise NotAVCSourceTree()
        self.wt = wt
        #print "wt:", wt
        #print "wt:", dir(wt)
        #print "wt.branch:", wt.branch
        #print "wt.branch:", dir(wt.branch)
        #print "wt.branch.nick:", wt.branch.nick
        #print "wt.branch.abspath:", wt.branch.abspath
        #print "wt.branch.base:", wt.branch.base
        #print "wt.branch.basis_tree:", wt.branch.basis_tree()

    def tree_root(self):
        proto,host,path,some,thing = urlparse.urlsplit(self.wt.branch.base)
        assert(proto == "file" and host == "")
        assert(some == "" and thing == "")
        return os.path.abspath(path)

    def branch_name(self):
        return self.wt.branch.nick


