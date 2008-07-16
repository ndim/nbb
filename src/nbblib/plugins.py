"""\
plugins.py - generic plugin system

Basic plugin architecture (metaclass tricks) by Marty Alchin from
http://gulopine.gamemusic.org/2008/jan/10/simple-plugin-framework/

GenericPluginMeta slightly modified to
 - store named plugins as dict
 - support plugin class hierarchies
Extended by GenericDetectPlugin to
 - support auto-detection of the adequate plugin

Example usage of the plugins module:

p = __import__(plugins)

Example non-auto-detection plugin:

class NonDetectPluginType(object):
    __metaclass__ = p.GenericPluginMeta

class PluginA(NonDetectPluginType):
    name = "PA"
class PluginB(NonDetectPluginType):
    name = "PB"

Example auto-detection plugin:

class MyPluginType(p.GenericDetectPlugin):
    __metaclass__ = p.GenericPluginMeta

    # The calling convention for constructor
    # detect(context, <mystuff...>)
    # is defined here, and the same <mystuff...> is used
    # to construct the exceptions.

    [no_match_exception = ...]
    [ambigous_match_exception = ...]
    [
    @classmethod
    def validate(cls, obj, context, *args, **kwargs):
        return True # or False, depending on params
    ]

class MyPluginA(MyPluginType):
    name = "MA"
    def __init__(self, context):
        super(MyPluginA, self).__init__(self, context)
        if not some_detection_successful:
            raise self.no_match_exception()
class MyPluginB(MyPluginType):
    name = "MB"
    def __init__(self, context):
        super(MyPluginB, self).__init__(self, context)
        if not other_detection_successful:
            raise self.no_match_exception()

"""


# TODO: Check plugin instances for defined members.
#  1. class AbstractMember(...): __get__, __set__
#  2. class ConcreteMember(...): __get__, __set__
#  3. plugin registration checks presence of AbstractMember instances,
#     and fails if one is found


import logging
import functools
import inspect


__all__ = []


__all__.append('NoPluginsRegistered')
class NoPluginsRegistered(Exception):
    """Raised when looking for plugins but none are registered"""
    def __init__(self, cls):
        super(NoPluginsRegistered, self).__init__()
        self.cls = cls
    def __str__(self):
        return "No plugins of type %s registered" % (self.cls.__name__)


__all__.append('DuplicatePluginName')
class DuplicatePluginName(Exception):
    """Raised when another plugin tries to register the same name"""
    def __init__(self, name, old, new):
        super(DuplicatePluginName, self).__init__()
        self.msg = "Duplicate plugin name %s, old plugin %s, new plugin %s" \
            % (repr(name), str(old), str(new))
    def __str__(self):
        return self.msg


__all__.append('PluginNoMatch')
class PluginNoMatch(Exception):
    """Raised when no registered plugin matches the given args"""
    def __init__(self, *args, **kwargs):
        super(PluginNoMatch, self).__init__()
        self.args = args
        self.kwargs = kwargs
    def __str__(self):
        return "%s(%s,%s)" % (self.__class__.__name__,
                              self.args, self.kwargs)


__all__.append('AmbigousPluginDetection')
class AmbigousPluginDetection(Exception):
    """Raised when more than one registered plugin matches the given args"""
    def __init__(self, matches, cls, context, *args, **kwargs):
        super(AmbigousPluginDetection, self).__init__()
        self.matches = matches
        self.cls = cls
        self.context = context
        self.args = args
        self.kwargs = kwargs
    def __str__(self):
        return "%s(%s.%s, %s, %s, %s, %s)" % (self.__class__.__name__,
                                              self.cls.__module__,
                                              self.cls.__name__,
                                              self.matches,
                                              self.context,
                                              self.args,
                                              self.kwargs)


__all__.append('AbstractMethodsInConcreteClass')
class AbstractMethodsInConcreteClass(Exception):
    """Raised when an abstract method is detected in a non-abstract class

    The method has been marked @abstractmethod in an ancestor, and must be
    implemented if this class is not abstract itself.
    """
    def __init__(self, cls, methods):
        super(AbstractMethodsInConcreteClass, self).__init__()
        self.cls = cls
        self.methods = methods
    def __str__(self):
        methods = " ".join((key for key, value in self.methods))
        return "Class %s.%s must implement the %s abstract methods." \
            % (self.cls.__module__,
               self.cls.__name__,
               methods)


__all__.append('AbstractMethodError')
class AbstractMethodError(Exception):
    """Raised when an abstract method is called"""
    def __init__(self, name, module):
        super(AbstractMethodError, self).__init__()
        self.name = name
        self.module = module
    def __str__(self):
        # FIXME: How to print class name alongside module and method name?
        return "Abstract method %s called someplace in %s" \
            % (repr(self.name), repr(self.module))


__all__.append('abstractmethod')
def abstractmethod(fun):
    """The decorator for abstract methods in plugins

    This decorator has two effects:
     * If the abstract method should ever be called, it will raise
       an AbstractMethodError.
     * If the class the method is defined has GenericPluginMeta as
       __metaclass__, __name__ is not None (i.e. it is a non-abstract
       Plugin class), and the method has not been overwritten with a
       method without @abstractmethod, there will be a
       AbstractMethodsInConcreteClass at module loading time, i.e.
       before the actual program is run!
    """
    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        # fun(self, *args, **kwargs)
        raise AbstractMethodError(name=fun.__name__,
                                  module=fun.__module__)
    wrapper.abstract_method = True
    return wrapper


# Internal type __all__.append('PluginDict')
class PluginDict(dict):
    """Helper for GenericPluginMeta class

    Behaves basically like a standard dict, but will raise an exception
    when asked to update an existing value.
    """

    # This is the important difference between PluginDict and dict.
    def __setitem__(self, key, value):
        if (key in self):
            old = self[key]
            if old.__name__ == value.__name__ and old.__module__ == value.__module__:
                pass
            else:
                raise DuplicatePluginName(name=key, old=self[key], new=value)
        else:
            super(PluginDict, self).__setitem__(key, value)


__all__.append('GenericPluginMeta')
class GenericPluginMeta(type):
    """Simple plugin metaclass with named plugins

    Simple usage:
    >>> class Plugin(object):
    ...     pass
    ...
    >>> class PluginA(Plugin):
    ...     __name__ = 'a'
    ...
    >>> class PluginA(Plugin):
    ...     __name__ = 'b'
    ...
    >>> print Plugin.plugins.keys()
    ['a', 'b']

    Advanced features:
    You can add abstract subclasses of Plugin by giving them a __name__ = None,
    define an @abstractmethod method in that abstract subclass, and much more.
    """
    def __init__(mcs, name, bases, attrs):
        super(GenericPluginMeta, mcs).__init__()
        logging.debug("META_INIT %s %s %s %s", mcs, name, bases, attrs)
        if not hasattr(mcs, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            mcs.plugins = PluginDict()
        elif mcs.name is not None:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            def abstract_method_filter(member):
                return hasattr(member, '__call__') \
                    and hasattr(member, 'abstract_method')
            ams = inspect.getmembers(mcs, abstract_method_filter)
            if ams:
                raise AbstractMethodsInConcreteClass(mcs, ams)
            logging.debug("Registering %s with %s as %s", mcs, mcs.plugins, mcs.name)
            mcs.plugins[mcs.name] = mcs
        else:
            # This must be an abstract subclass of plugins.
            pass


__all__.append('GenericDetectPlugin')
class GenericDetectPlugin(object):
    """Advanced plugin class where the plugins detect whether they apply

    Use it by defining a subclass with the proper properties and methods overwritten.

    Example:
    >>> class FooDetectPlugin(GenericDetectPlugin):
    ...     @classmethod
    ...     def validate(cls, obj, context, foo, bar):
    ...         return cls.__name__ == 'A'
    ... 
    >>> class FooDetectPluginA(FooDetectPlugin):
    ...     __name__ = 'A'
    ... 
    >>> class FooDetectPluginB(FooDetectPlugin):
    ...     __name__ = 'B'
    ... 
    >>> FooDetectPlugin.detect('FOO', 'BAR')
    """

    """You may override this with a more plugin specific subclass of PluginNoMatch"""
    no_match_exception = PluginNoMatch
    """You may override this with a more plugin specific subclass of AmbigousPluginDetection"""
    ambigous_match_exception = AmbigousPluginDetection

    def __init__(self, context):
        super(GenericDetectPlugin, self).__init__()
        self.context = context

    @classmethod
    def validate(cls, obj, context, *args, **kwargs):
        """Override this in subclass to validate the given args

        @context Context information
        @param cls subclass of GenericDetectPlugin and type of obj
        @param obj instance of cls which is to be validated
        @param args the same args as given to detect()
        @param kwargs the same kwargs as given to detect()
        """
        logging.debug("GDval")
        return True

    @classmethod
    def detect(cls, context, *args, **kwargs):
        """Detect which plugin matches the given arguments

        It might make sense to document the exact calling conventions in
        derived classes:

        >>> class FooDetectPlugin(GenericDetectPlugin):
        ...     @classmethod
        ...     def detect(cls, context, foo, bar):
        ...         "detect plugin from foo and bar values yadda yadda"
        ...         return super(FooDetectPlugin, cls).detect(cls, context, foo, bar)
        """
        logging.debug("DETECT %s", cls)
        if len(cls.plugins) < 1:
            raise NoPluginsRegistered(cls)
        matches = PluginDict()
        for key, klass in cls.plugins.iteritems():
            try:
                t = klass(context, *args, **kwargs)
                logging.debug("KLASS %s unvalidated, %s", klass,
                              klass.validate)
                if klass.validate(t, context, *args, **kwargs):
                    logging.debug("KLASS %s validated", klass)
                    matches[key] = t
            except PluginNoMatch:
                pass # ignore non-matching plugins
        logging.debug("Matches: %s", matches)
        if len(matches) > 1:
            raise cls.ambigous_match_exception(matches,
                                               cls, context,
                                               *args, **kwargs)
        elif len(matches) < 1:
            raise cls.no_match_exception(*args, **kwargs)
        logging.debug("Returning match from %s", matches)
        return matches[matches.keys()[0]]


