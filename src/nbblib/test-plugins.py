#!/usr/bin/python
"""Test newplugins module"""

import logging
import sys

logging.basicConfig(level = logging.DEBUG,
                    format = "%(levelname)s: %(message)s",
                    stream = sys.stderr)
if True:
   logging.debug("xxx debug")
   logging.info("xxx info")
   logging.warning("xxx warn")
   logging.error("xxx error")


from plugins import *

# Not for __all__
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
        def validate(cls, obj, context, *args, **kwargs):
            logging.debug("Aval")
            return False


    class TestDetectPluginB(GenericDetectPlugin):
        __metaclass__ = GenericPluginMeta


    class TestDetectPluginC(GenericDetectPlugin):
        __metaclass__ = GenericPluginMeta
        @classmethod
        def validate(cls, obj, context, *args, **kwargs):
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
        def validate(cls, obj, context, *args, **kwargs):
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

selftest()

