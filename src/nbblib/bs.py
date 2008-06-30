########################################################################
# Buildsystem Source Tree plugins
########################################################################


import os
import logging

from nbblib import progutils
from nbblib import plugins


__all__ = []


class NotABSSourceTree(plugins.PluginNoMatch):
    def __init__(self, vcs_tree):
        super(NotABSSourceTree, self).__init__()
        self.vcs_tree = vcs_tree
    def __str__(self):
        return "Unknown BS source tree type: %s" % repr(self.vcs_tree.tree_root)


class AmbigousBSDetection(plugins.AmbigousPluginDetection):
    def __init__(self, matches, cls, context, vcs_tree):
        super(AmbigousBSDetection, self).__init__(matches, cls, context)
        self.vcs_tree = vcs_tree
    def __str__(self):
        alist = self.matches.keys()
        alist.sort()
        return "Ambigous BS types detected for %s:\n  %s" % (repr(self.vcs_tree.tree_root),
                                                         '\n  '.join(alist))


__all__.append('BSSourceTree')
class BSSourceTree(plugins.GenericDetectPlugin):
    __metaclass__ = plugins.GenericPluginMeta
    no_match_exception = NotABSSourceTree
    ambigous_match_exception = AmbigousBSDetection

    @classmethod
    def validate(cls, obj, vcs_tree):
        logging.debug("BSSourceTree.validate(%s, %s, %s) %s %s",
                      cls, obj, vcs_tree,
                      repr(obj.tree_root), repr(vcs_tree.tree_root))
        return obj.tree_root == vcs_tree.tree_root


    def get_tree_root(self): return self._get_tree_root()
    tree_root = property(get_tree_root)


    def __str__(self):
        return "BS-Source-Tree(%s, %s)" % (self.name,
                                           repr(self.tree_root))

    # Abstract methods
    @plugins.abstractmethod
    def _get_tree_root(self): pass
    @plugins.abstractmethod
    def init(self): pass
    @plugins.abstractmethod
    def configure(self): pass
    @plugins.abstractmethod
    def build(self): pass
    @plugins.abstractmethod
    def install(self): pass


class AutomakeSourceTree(BSSourceTree):
    name = 'automake'
    def __init__(self, context, vcs_tree):
        super(AutomakeSourceTree, self).__init__(context)
        srcdir = vcs_tree.tree_root
        self.config = vcs_tree.config
        flag = False
        for f in [ os.path.join(srcdir, 'configure.ac'),
                   os.path.join(srcdir, 'configure.in'),
                   ]:
            if os.path.exists(f):
                flag = True
                break
        if not flag:
            raise self.no_match_exception(vcs_tree)

    def _get_tree_root(self):
        return self.config.srcdir

    def init(self):
        """'autoreconf'"""
        progutils.prog_run(["autoreconf", "-v", "-i", "-s", self.config.srcdir],
                           self.context)

    def configure(self):
        """'configure --prefix'"""
        if not os.path.exists(os.path.join(self.config.srcdir, 'configure')):
            self.init()
        builddir = self.config.builddir
        if not os.path.exists(builddir): os.makedirs(builddir)
        os.chdir(builddir)
        progutils.prog_run(["%s/configure" % self.config.srcdir,
                            "--prefix=%s" % self.config.installdir,
                            "--enable-maintainer-mode",
                            ], self.context)

    def build(self):
        """'make'"""
        builddir = self.config.builddir
        if not os.path.exists(os.path.join(builddir, 'config.status')):
            self.configure()
        os.chdir(builddir)
        progutils.prog_run(["make", ], self.context)

    def install(self):
        """'make install'"""
        builddir = self.config.builddir
        if not os.path.exists(os.path.join(builddir, 'config.status')):
            self.configure()
        os.chdir(builddir)
        progutils.prog_run(["make", "install", "INSTALL=/usr/bin/install -p"],
                           self.context)


class SconsSourceTree(BSSourceTree):
    name = 'scons'
    def __init__(self, context, vcs_tree):
        super(SconsSourceTree, self).__init__(context)
        srcdir = vcs_tree.tree_root
        self.config = vcs_tree.config
        flag = False
        for f in [ os.path.join(srcdir, 'SConstruct'),
                   ]:
            if os.path.exists(f):
                flag = True
                break
        if not flag:
            raise self.no_match_exception(vcs_tree)
        self.__tree_root = srcdir

    def _get_tree_root(self):
        return self.__tree_root

    def init(self): pass
    def configure(self): pass

    def build(self):
        progutils.prog_run(["scons"],
                           self.context)

    def install(self):
        progutils.prog_run(["scons", "install"],
                           self.context)

