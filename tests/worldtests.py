#!/usr/bin/env python
import sys,os
import tempfile, shutil
from io import BytesIO
import logging
import random
import time
import zlib

import unittest
try:
    from unittest import skip as _skip
except ImportError:
    # Python 2.6 has an older unittest API. The backported package is available from pypi.
    import unittest2 as unittest

# Search parent directory first, to make sure we test the local nbt module, 
# not an installed nbt module.
parentdir = os.path.realpath(os.path.join(os.path.dirname(__file__),os.pardir))
if parentdir not in sys.path:
    sys.path.insert(1, parentdir) # insert ../ just after ./

from nbt.world import WorldFolder
from nbt.region import RegionFile

WORLD_TEST_FOLDER = os.path.join(os.path.dirname(__file__), 'world_test')
REGION_X=4
REGION_Z=-4

### Actual Test Classes ###

class WorldTest(unittest.TestCase):
    """Test world."""

    def testGetRegion(self):
        """
        get_region() should return a region object for existing regions
        """
        world = WorldFolder(WORLD_TEST_FOLDER)
        region = world.get_region(REGION_X, REGION_Z)
        self.assertIsInstance(region, RegionFile)

    def testGetRegionCache(self):
        """
        get_region() should return the same region instance for subsequent calls
        """
        world = WorldFolder(WORLD_TEST_FOLDER)
        region1 = world.get_region(REGION_X, REGION_Z)
        region2 = world.get_region(REGION_X, REGION_Z)
        self.assertIs(region2, region1)

    def testGetRegionReloadClosed(self):
        """
        get_region() should reload closed regions
        """
        world = WorldFolder(WORLD_TEST_FOLDER)
        region1 = world.get_region(REGION_X, REGION_Z)
        region1.close()
        region2 = world.get_region(REGION_X, REGION_Z)
        self.assertIsNot(region2, region1)


if __name__ == '__main__':
    logger = logging.getLogger("nbt.tests.worldtests")
    if len(logger.handlers) == 0:
        # Logging is not yet configured. Configure it.
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
    unittest.main()
