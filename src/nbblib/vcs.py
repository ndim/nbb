import os
import logging
import urlparse
import itertools

from nbblib import package
from nbblib import progutils
from nbblib import plugins


__all__ = []


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

class NotAVCSourceTree(plugins.PluginNoMatch):
    def __init__(self, srcdir):
        super(NotAVCSourceTree, self).__init__()
        self.srcdir = srcdir
    def __str__(self):
        return "Unknown VCS source tree type: %s" % repr(self.srcdir)


class AmbigousVCSDetection(plugins.AmbigousPluginDetection):
    def __init__(self, matches, cls, context, srcdir):
        super(AmbigousVCSDetection, self).__init__(matches, cls, context)
        self.srcdir = srcdir
    def __str__(self):
        # We possibly need to re-add m.tree_root here again soon
        alist = itertools.chain([('VCS type', 'Branch name', )],
                                (((name, m.branch_name, )
                                 for name, m in self.matches.iteritems())))
        table = "\n".join(["  %-9s %s" % a for a in alist])
        return "Ambigous VCS types detected for %s:\n%s" % (repr(self.srcdir), table)


__all__.append('VCSourceTree')
class VCSourceTree(plugins.GenericDetectPlugin):
    """
    Mount point for plugins which refer to actions that can be performed.

    Plugins implementing this reference must provide the following
    interface:

    name  attribute
        The text to be displayed, describing the version control system
    __init__
        Must "raise self.no_match_exception()" if it does not match.
    and the other abstract methods below
    """
    __metaclass__ = plugins.GenericPluginMeta
    no_match_exception = NotAVCSourceTree
    ambigous_match_exception = AmbigousVCSDetection

    @classmethod
    def validate(cls, obj, srcdir):
        logging.debug("cls %s", cls)
        logging.debug("obj %s", obj)
        logging.debug("srcdir %s", srcdir)
        return obj.tree_root == srcdir

    @classmethod
    def detect(cls, context, srcdir):
        """Examine srcdir for VCS system and return proper VCSourceTree obj

        @param srcdir string with absolute path of source code directory
        """
        super(VCSourceTree, cls).detect(context, srcdir)

    def get_config(self):
        """Get configuration object which determines builddir etc"""
        return AbstractConfig(self.tree_root, self.branch_name)
    config = property(get_config)

    @plugins.abstractmethod
    def _get_tree_root(self):
        """Get absolute path to source tree root"""
        pass

    def get_tree_root(self):
        return self._get_tree_root()
    tree_root = property(get_tree_root)

    @plugins.abstractmethod
    def _get_branch_name(self):
        """Return name identifying the branch"""
        pass
    def get_branch_name(self):
        """Return name identifying the branch"""
        return self._get_branch_name()
    branch_name = property(get_branch_name)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "<%s(%s, %s)>" % (self.__class__.__name__,
                                 repr(self.tree_root),
                                 repr(self.branch_name))


########################################################################
# VCS Source Tree plugins
########################################################################

class GitSourceTree(VCSourceTree):

    name = 'git'

    def __init__(self, context, srcdir):
        super(GitSourceTree, self).__init__(context)
        os.chdir(srcdir)
        if "true" != progutils.prog_stdout(["git", "rev-parse",
                                            "--is-inside-work-tree"]):
            raise self.no_match_exception(srcdir)
        reldir = progutils.prog_stdout(["git", "rev-parse", "--show-cdup"])
        if reldir:
            os.chdir(reldir)
        self.__tree_root = os.getcwd()

    def get_config(self):
        return GitConfig(self.tree_root, self.branch_name)
    config = property(get_config)

    def _get_tree_root(self):
        return self.__tree_root

    def _get_branch_name(self):
        bname = progutils.prog_stdout(["git", "symbolic-ref", "HEAD"])
        refs,heads,branch = bname.split('/')
        assert(refs=='refs' and heads=='heads')
        return branch


class GitConfig(AbstractConfig):
    """git config interface"""

    def __init__(self, *args, **kwargs):
        super(GitConfig, self).__init__(*args, **kwargs)

    def _itemname(self, item): return '.'.join((package.GIT_CONFIG_PREFIX, item, ))
    def _myreldir(self, rdir):
        return os.path.join(self._srcdir, rdir, self._nick)

    def get_builddir(self):
        ret, stdout, stderr = progutils.prog_retstd(['git', 'config', self._itemname('builddir')])
        assert(stderr == "")
	if ret == 0 and stdout:
            return self._myreldir(stdout)
        else:
            return super(GitConfig, self).get_builddir()

    def set_builddir(self, value):
        ret, stdout, stderr = progutils.prog_retstd(['git', 'config', self._itemname('builddir'), value])
        assert(ret == 0 and stdout == "" and stderr == "")

    builddir = property(get_builddir, set_builddir)

    def get_installdir(self):
        ret, stdout, stderr = progutils.prog_retstd(['git', 'config', self._itemname('installdir')])
        assert(stderr == "")
	if ret == 0 and stdout:
            return self._myreldir(stdout)
        else:
            return super(GitConfig, self).get_installdir()

    def set_installdir(self, value):
        ret, stdout, stderr = progutils.prog_retstd(['git', 'config', self._itemname('installdir'), value])
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
            raise self.no_match_exception(srcdir)
        except ImportError:
            raise self.no_match_exception(srcdir)
        self.wt = wt
        #print "wt:", wt
        #print "wt:", dir(wt)
        #print "wt.branch:", wt.branch
        #print "wt.branch:", dir(wt.branch)
        #print "wt.branch.nick:", wt.branch.nick
        #print "wt.branch.abspath:", wt.branch.abspath
        #print "wt.branch.base:", wt.branch.base
        #print "wt.branch.basis_tree:", wt.branch.basis_tree()

    def _get_tree_root(self):
        proto,host,path,some,thing = urlparse.urlsplit(self.wt.branch.base)
        assert(proto == "file" and host == "")
        assert(some == "" and thing == "")
        return os.path.abspath(path)

    def _get_branch_name(self):
        return self.wt.branch.nick


