import sys


class DuplicatePluginName(Exception):
    pass


class PluginDict(object):
    """Helper for GenericPluginMeta class

    Behaves basically like a standard dict, but will raise an exception
    when asked to update an existing value.
    """
    def __init__(self):
        self.dict = {}

    # This is the important difference between PluginDict and dict.
    def __setitem__(self, key, value):
        if self.dict.has_key(key):
            raise DuplicatePluginName()
        else:
            self.dict[key] = value

    # Forward all other dict methods.
    def __getitem__(self, *args): return self.dict.__getitem__(*args)
    def items(self): return self.dict.items()
    def iteritems(self): return self.dict.iteritems()
    def keys(self): return self.dict.keys()
    def values(self): return self.dict.values()
    def __iter__(self): return self.dict.__iter__()
    def __str__(self): return self.dict.__str__()
    def __repr__(self): return self.dict.__repr__()
    def __len__(self): return self.dict.__len__()
    def has_key(self, key): return self.dict.has_key(key)


########################################################################
# Generic plugin system
########################################################################
# Plugin architecture (metaclass tricks) by Marty Alchin from
# http://gulopine.gamemusic.org/2008/jan/10/simple-plugin-framework/
# Slightly modified go store plugins as dict.
########################################################################


class NoPluginsRegistered(Exception):
    def __init__(self, cls):
        super(NoPluginsRegistered, self).__init__()
        self.cls = cls
    def __str__(self):
        return "No %s plugins registered" % (self.cls.__name__)
    

class GenericPluginMeta(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = PluginDict()
        elif hasattr(cls, 'name'):
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins[cls.name] = cls
        else:
            # This must be an abstract subclass of plugins.
            pass

