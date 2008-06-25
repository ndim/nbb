########################################################################
# Buildsystem Source Tree plugins
########################################################################


import os
import logging

from nbblib.plugins import *
from nbblib.progutils import *


class NotABSSourceTree(Exception):
    def __init__(self, vcs_tree):
        super(NotABSSourceTree, self).__init__()
        self.vcs_tree = vcs_tree
    def __str__(self):
        return ("Source tree build system type for '%s' not detected"
                % (self.vcs_tree,))


class AmbigousBSSource(Exception):
    def __init__(self, srcdir, matches):
        super(AmbigousBSSource, self).__init__()
        self.srcdir = srcdir
        self.matches = matches
    def __str__(self):
        fmt = "  %-9s %s"
        def strmatch(m):
            return fmt % (m.name, m.tree_root())
        alist = [fmt % ('VCS Type', 'Source tree root')]
        alist.extend(map(strmatch, self.matches))
        return ("More than one source tree VCS type detected for '%s':\n#%s"
                % (self.srcdir, '\n '.join(alist)))


class BSSourceTree(object):
    __metaclass__ = GenericPluginMeta

    def __init__(self, context):
        super(BSSourceTree, self).__init__()
        self.context = context

    @classmethod
    def detect(cls, vcs_tree, context):
        """Find BS tree type and return it"""
        if len(cls.plugins) < 1:
            raise NoPluginsRegistered(cls)
        #logging.debug("CLASS %s", cls)
        matches = PluginDict()
        for key, klass in cls.plugins.iteritems():
            try:
                t = klass(vcs_tree, context)
                if t.tree_root() == vcs_tree.tree_root():
                    #logging.debug("KLASS %s", klass)
                    matches[key] = t
            except NotABSSourceTree, e:
                pass
        if len(matches) > 1:
            raise ("More than one source tree BS type detected for '%s': %s"
                   % (vcs_tree, ", ".join([str(x) for x in matches])))
        elif len(matches) < 1:
            raise NotABSSourceTree(vcs_tree)
        return matches[matches.keys()[0]]

    def __str__(self):
        return "BS-Source-Tree(%s, %s)" % (self.name,
                                           repr(self.tree_root()))

    # Abstract methods
    def tree_root(self): raise NotImplementedError()
    def init(self): raise NotImplementedError()
    def configure(self): raise NotImplementedError()
    def build(self): raise NotImplementedError()
    def install(self): raise NotImplementedError()


class AutomakeSourceTree(BSSourceTree):
    name = 'automake'
    def __init__(self, vcs_tree, context):
        super(AutomakeSourceTree, self).__init__(context)
        srcdir = vcs_tree.tree_root()
        self.config = vcs_tree.config
        flag = False
        for f in [ os.path.join(srcdir, 'configure.ac'),
                   os.path.join(srcdir, 'configure.in'),
                   ]:
            if os.path.exists(f):
                flag = True
                break
        if not flag:
            raise NotABSSourceTree(vcs_tree)

    def tree_root(self):
        return self.config.srcdir

    def init(self):
        """'autoreconf'"""
        prog_run(["autoreconf", "-v", "-i", "-s", self.config.srcdir],
                 self.context)

    def configure(self):
        """'configure --prefix'"""
        if not os.path.exists(os.path.join(self.config.srcdir, 'configure')):
            self.init()
        builddir = self.config.builddir
        if not os.path.exists(builddir): os.makedirs(builddir)
        os.chdir(builddir)
        prog_run(["%s/configure" % self.config.srcdir,
                  "--prefix=%s" % self.config.installdir,
                  "--enable-maintainer-mode",
                  ], self.context)

    def build(self):
        """'make'"""
        builddir = self.config.builddir
        if not os.path.exists(os.path.join(builddir, 'config.status')):
            self.configure()
        os.chdir(builddir)
        prog_run(["make", ], self.context)

    def install(self):
        """'make install'"""
        builddir = self.config.builddir
        if not os.path.exists(os.path.join(builddir, 'config.status')):
            self.configure()
        os.chdir(builddir)
        prog_run(["make", "install", "INSTALL=/usr/bin/install -p"],
                 self.context)


