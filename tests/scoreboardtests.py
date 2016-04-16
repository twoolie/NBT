#!/usr/bin/env python
import sys,os
import tempfile, shutil
from io import BytesIO
from gzip import GzipFile

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
    sys.path.insert(1, parentdir)  # insert ../ just after ./

from nbt.nbt import _TAG_Numeric, TAG_Int, MalformedFileError, NBTFile, TAGLIST

NBTTESTFILE = os.path.join(os.path.dirname(__file__), 'scoreboard.dat')

class ScoreboardTest(unittest.TestCase):
    """test scoreboard reading"""

    def setUp(self):
        self.scores = NBTFile(NBTTESTFILE,'rb')

    def testReadScoreboard(self):
        ps = self.scores["data"]["PlayerScores"]

        # {TAG_String(u'Objective'): Diamond, TAG_Byte(u'Locked'): 0,
        # TAG_Int(u'Score'): 0, TAG_String(u'Name'): soulthps}
        self.assertEqual(str(ps[0]["Objective"]), 'Diamond')
        self.assertEqual(str(ps[0]["Name"]), 'soulthps')
        self.assertEqual(str(ps[0]["Score"]), '0')
        
        # {TAG_String(u'Objective'): Time, TAG_Byte(u'Locked'): 0,
        # TAG_Int(u'Score'): 19238, TAG_String(u'Name'): soulthps}
        self.assertEqual(str(ps[2]["Objective"]), 'Time')
        self.assertEqual(str(ps[2]["Name"]), 'soulthps')
        self.assertEqual(str(ps[2]["Score"]), '19238')

        # {TAG_String(u'Objective'): Diamond, TAG_Byte(u'Locked'): 0,
        # TAG_Int(u'Score'): 77, TAG_String(u'Name'): fwaggle}
        self.assertEqual(str(ps[3]["Objective"]), 'Diamond')
        self.assertEqual(str(ps[3]["Name"]), 'fwaggle')
        self.assertEqual(str(ps[3]["Score"]), '77')

        # {TAG_String(u'Objective'): Deaths, TAG_Byte(u'Locked'): 0,
        # TAG_Int(u'Score'): 7, TAG_String(u'Name'): DuncanDonutz}
        self.assertEqual(str(ps[14]["Objective"]), 'Deaths')
        self.assertEqual(str(ps[14]["Name"]), 'DuncanDonutz')
        self.assertEqual(str(ps[14]["Score"]), '7')

if __name__ == '__main__':
    unittest.main()
