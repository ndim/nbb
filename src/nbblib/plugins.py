"""\
plugins.py - generic plugin system

Basic plugin architecture (metaclass tricks) by Marty Alchin from
http://gulopine.gamemusic.org/2008/jan/10/simple-plugin-framework/

GenericPluginMeta slightly modified to
 - store plugins as dict
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
    def validate(cls, obj, *args, **kwargs):
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


import sys
import logging
import types
import functools
import inspect


class NoPluginsRegistered(Exception):
    def __init__(self, cls):
        super(NoPluginsRegistered, self).__init__()
        self.cls = cls
    def __str__(self):
        return "No plugins of type %s registered" % (self.cls.__name__)


class DuplicatePluginName(Exception):
    pass


class PluginNoMatch(Exception):
    def __init__(self, *args, **kwargs):
        super(PluginNoMatch, self).__init__()
        self.args = args
        self.kwargs = kwargs
    def __str__(self):
        return "%s(%s,%s)" % (self.__class__.__name__,
                              self.args, self.kwargs)


class AmbigousPluginDetection(Exception):
    def __init__(self, matches, cls, context, *args, **kwargs):
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


class AbstractMethodsInConcreteClass(Exception):
    def __init__(self, cls, methods):
        self.cls = cls
        self.methods = methods
    def __str__(self):
        methods = " ".join((k for k,v in self.methods))
        return "Class %s.%s must implement the %s abstract methods." \
            % (self.cls.__module__,
               self.cls.__name__,
               methods)


class AbstractMethodError(Exception):
    def __init__(self, name, module):
        self.name = name
        self.module = module
    def __str__(self):
        # FIXME: Class name?
        return "Abstract method %s called someplace in %s" \
            % (repr(self.name), repr(self.module))


def abstractmethod(fun):
    @functools.wraps(fun)
    def f(self, *args, **kwargs):
        # fun(self, *args, **kwargs)
        raise AbstractMethodError(name=fun.__name__,
                                  module=fun.__module__)
    f.abstract_method = True
    return f


class PluginDict(dict):
    """Helper for GenericPluginMeta class

    Behaves basically like a standard dict, but will raise an exception
    when asked to update an existing value.
    """

    # This is the important difference between PluginDict and dict.
    def __setitem__(self, key, value):
        if self.has_key(key):
            raise DuplicatePluginName()
        else:
            super(PluginDict, self).__setitem__(key, value)


class GenericPluginMeta(type):
    def __init__(cls, name, bases, attrs):
        logging.debug("META_INIT %s %s %s %s", cls, name, bases, attrs)
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = PluginDict()
        elif cls.name is not None:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            logging.debug("Registering %s together with %s", cls, cls.plugins)
            def abstract_method_filter(member):
                return hasattr(member, '__call__') \
                    and hasattr(member, 'abstract_method')
            ams = inspect.getmembers(cls, abstract_method_filter)
            if ams:
                raise AbstractMethodsInConcreteClass(cls, ams)
            cls.plugins[cls.name] = cls
        else:
            # This must be an abstract subclass of plugins.
            pass


class GenericDetectPlugin(object):
    no_match_exception = PluginNoMatch
    ambigous_match_exception = AmbigousPluginDetection

    def __init__(self, context):
        super(GenericDetectPlugin, self).__init__()
        self.context = context

    @classmethod
    def validate(cls, obj, *args, **kwargs):
        logging.debug("GDval")
        return True

    @classmethod
    def detect(cls, context, *args, **kwargs):
        """Detect stuff"""
        logging.debug("DETECT %s", cls)
        if len(cls.plugins) < 1:
            raise NoPluginsRegistered(cls)
        matches = PluginDict()
        for key, klass in cls.plugins.iteritems():
            try:
                t = klass(context, *args, **kwargs)
                logging.debug("KLASS %s unvalidated, %s", klass,
                              klass.validate)
                if klass.validate(t, *args, **kwargs):
                    logging.debug("KLASS %s validated", klass)
                    matches[key] = t
            except PluginNoMatch, e:
                pass
        if len(matches) > 1:
            raise cls.ambigous_match_exception(matches,
                                               cls, context,
                                               *args, **kwargs)
        elif len(matches) < 1:
            raise cls.no_match_exception(*args, **kwargs)
        return matches[matches.keys()[0]]


def selftest():

    class PluginNoMatchA(PluginNoMatch):
        pass
    class AmbigousPluginDetectionA(AmbigousPluginDetection):
        pass


    class TestDetectPluginA(GenericDetectPlugin):
        __metaclass__ = GenericPluginMeta
        no_match_exception = PluginNoMatchA
        ambigous_match_exception = AmbigousPluginDetectionA
        @classmethod
        def validate(cls, obj, *args, **kwargs):
            logging.debug("Aval")
            return False


    class TestDetectPluginB(GenericDetectPlugin):
        __metaclass__ = GenericPluginMeta


    class TestDetectPluginC(GenericDetectPlugin):
        __metaclass__ = GenericPluginMeta
        @classmethod
        def validate(cls, obj, *args, **kwargs):
            logging.debug("Cval")
            return False


    class TestDetectPluginA1(TestDetectPluginA):
        name = "A1"
    class TestDetectPluginA2(TestDetectPluginA):
        name = "A2"
    class TestDetectPluginA3(TestDetectPluginA):
        name = "A3"

    class TestDetectPluginB1(TestDetectPluginB):
        name = "B1"
    class TestDetectPluginB2(TestDetectPluginB):
        name = "B2"
    class TestDetectPluginB3(TestDetectPluginB):
        name = "B3"

    class TestDetectPluginC1(TestDetectPluginC):
        name = "C1"
    class TestDetectPluginC2(TestDetectPluginC):
        name = "C2"
    class TestDetectPluginC3(TestDetectPluginC):
        name = "C3"
        @classmethod
        def validate(cls, obj, *args, **kwargs):
            logging.debug("C3val")
            return True

    ctx = None

    print "GenericPluginMeta", dir(GenericPluginMeta)
    print "GenericDetectPlugin", dir(GenericDetectPlugin)
    print "TestDetectPluginA", dir(TestDetectPluginA)
    print "TestDetectPluginA", dir(TestDetectPluginA)
    print "TestDetectPluginB", dir(TestDetectPluginB)
    print "TestDetectPluginC", dir(TestDetectPluginC)

    try:
        a = TestDetectPluginA.detect(ctx)
    except:
        logging.error("aaaa", exc_info=True)

    try:
        b = TestDetectPluginB.detect(ctx)
    except:
        logging.error("bbbb", exc_info=True)

    try:
        c = TestDetectPluginC.detect(ctx)
    except:
        logging.error("cccc", exc_info=True)
