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


import plugins
plugins.selftest()

