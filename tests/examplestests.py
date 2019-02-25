#!/usr/bin/env python
# encoding: utf-8
"""
Run all scripts in examples on specific sample world.
"""

import sys
import os
import subprocess
import shutil
import tempfile
import glob
import logging

import unittest
try:
    from unittest import skip as _skip
except ImportError:
    # Python 2.6 has an older unittest API. The backported package is available from pypi.
    import unittest2 as unittest

# local modules
import downloadsample

if sys.version_info[0] < 3:
    def _deletechars(text, deletechars):
        """Return string, with the deletechars removed"""
        return filter(lambda c: c not in deletechars, text)
else:
    def _deletechars(text, deletechars):
        """Return string, with the deletechars removed"""
        filter = str.maketrans('', '', deletechars)
        return text.translate(filter)

def _mkdir(dstdir, subdir):
    """Helper function: create folder /dstdir/subdir"""
    os.mkdir(os.path.join(dstdir, os.path.normpath(subdir)))
def _copyglob(srcdir, destdir, pattern):
    """Helper function: copies files from /srcdir/pattern to /destdir/pattern.
    pattern is a glob pattern."""
    for fullpath in glob.glob(os.path.join(srcdir, os.path.normpath(pattern))):
        relpath = os.path.relpath(fullpath, srcdir)
        shutil.copy2(fullpath, os.path.join(destdir, relpath))
def _copyrename(srcdir, destdir, src, dest):
    """Helper function: copy file from /srcdir/src to /destdir/dest."""
    shutil.copy2(os.path.join(srcdir, os.path.normpath(src)), \
                os.path.join(destdir, os.path.normpath(dest)))


class ScriptTestCase(unittest.TestCase):
    """Test Case with helper functions for running a script, and installing a 
    Minecraft sample world."""
    worldfolder = None
    mcregionfolder = None
    anvilfolder = None
    examplesdir = os.path.normpath(os.path.join(__file__, os.pardir, os.pardir, 'examples'))
    def runScript(self, script, args):
        scriptpath = os.path.join(self.examplesdir, script)
        args.insert(0, scriptpath)
        # Ensure we're using the same python version.
        # python = sys.argv[0]
        # args.insert(0, python)
        env = dict(os.environ).copy()
        env['LC_ALL'] = 'C'
        # Open a subprocess, wait till it is done, and get the STDOUT result
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        p.wait()
        output = [r.decode('utf-8') for r in p.stdout.readlines()]
        for l in p.stderr.readlines():
            sys.stdout.write("%s: %s" % (script, l.decode('utf-8')))
        try:
            p.stdout.close()
            p.stderr.close()
        except IOError:
            pass
        self.assertEqual(p.returncode, 0, "return code is %d" % p.returncode)
        return output
    def assertEqualOutput(self, actual, expected):
        """Compare two lists of strings, ignoring whitespace at begin and end of line."""
        if len(actual) < len(expected):
            self.fail("Output is %d lines, expected at least %d lines" % \
                    (len(actual), len(expected)))
        for i,expline in enumerate(expected):
            self.assertEqual(actual[i].strip(), expline.strip(), \
                    "Output line %d is %r, expected %r" % (i+1, actual[i], expline))
    def assertEqualString(self, actual, expected):
        """Compare strings, ignoring whitespace at begin and end of line."""
        self.assertEqual(actual.strip(), expected.strip(), \
                    "Output line %r, expected %r" % (actual, expected))


class BiomeAnalysisScriptTest(ScriptTestCase):
    pass
    
    # TODO: Sample World was converted with simple script, but does not seem to have biome data.
    # This needs to be added. (opening the world with minecraft client will change the 
    # world a bit, which I like to avoid. Perhaps opening with the server will not change it, 
    # if "/stop" is called quickly enough. this may change the amount of generated chunks to 
    # everything in a 380x380 block though.)
    
    # @classmethod
    # def setUpClass(cls):
    #   cls.installsampleworld()
    #   cls.extractAnvilWorld()
    # def testAnvilWorld(self):
    #   output = self.runScript('biome_analysis.py', [self.anvilfolder])

class BlockAnalysisScriptTest(ScriptTestCase):

    def testMcRegionWorld(self):
        output = self.runScript('block_analysis.py', [self.mcregionfolder])
        self.assertTrue(len(output) == 60, "Expected output of 60 lines long")
        self.assertEqualString(output[-1], '21397504 total blocks in world, 11181987 are non-air (52.2584%)')

    def testAnvilWorld(self):
        output = self.runScript('block_analysis.py', [self.anvilfolder])
        self.assertTrue(len(output) == 60, "Expected output of 60 lines long")
        self.assertEqualString(output[-1], '13819904 total blocks in world, 11181987 are non-air (80.9122%)')


class ChestAnalysisScriptTest(ScriptTestCase):
    def testMcRegionWorld(self):
        output = self.runScript('chest_analysis.py', [self.mcregionfolder])
        self.assertEqual(len(output), 178)
        count = len(list(filter(lambda l: l.startswith('Chest at '), output)))
        self.assertEqual(count, 38)
    def testAnvilWorld(self):
        output = self.runScript('chest_analysis.py', [self.anvilfolder])
        self.assertEqual(len(output), 178)
        count = len(list(filter(lambda l: l.startswith('Chest at '), output)))
        self.assertEqual(count, 38)


def has_PIL():
    try:
        from PIL import Image
        return True
    except ImportError:
        return False


class MapScriptTest(ScriptTestCase):
    @unittest.skipIf(not has_PIL(), "PIL library not available")
    def testMcRegionWorld(self):
        output = self.runScript('map.py', ['--noshow', self.mcregionfolder])
        self.assertTrue(output[-1].startswith("Saved map as "))
    # TODO: this currently writes the map to tests/nbtmcregion*.png files. 
    # The locations should be a tempfile, and the file should be deleted afterwards.
    
    @unittest.skipIf(not has_PIL(), "PIL library not available")
    def testAnvilWorld(self):
        output = self.runScript('map.py', ['--noshow', self.anvilfolder])
        self.assertTrue(output[-1].startswith("Saved map as "))
    # TODO: same as above


class MobAnalysisScriptTest(ScriptTestCase):
    def testMcRegionWorld(self):
        output = self.runScript('mob_analysis.py', [self.mcregionfolder])
        self.assertEqual(len(output), 413)
        output = sorted(output)
        self.assertEqualString(output[0], "Chicken at 107.6,88.0,374.5")
        self.assertEqualString(output[400], "Zombie at 249.3,48.0,368.1")
    def testAnvilWorld(self):
        output = self.runScript('mob_analysis.py', [self.anvilfolder])
        self.assertEqual(len(output), 413)
        output = sorted(output)
        self.assertEqualString(output[0], "Chicken at 107.6,88.0,374.5")
        self.assertEqualString(output[400], "Zombie at 249.3,48.0,368.1")

class SeedScriptTest(ScriptTestCase):
    def testMcRegionWorld(self):
        output = self.runScript('seed.py', [self.mcregionfolder])
        self.assertEqualOutput(output, ["-3195717715052600521"])
    def testAnvilWorld(self):
        output = self.runScript('seed.py', [self.anvilfolder])
        self.assertEqualOutput(output, ["-3195717715052600521"])

class GenerateLevelDatScriptTest(ScriptTestCase):
    expected = [
        "NBTFile('Data'): {10 Entries}",
        "{",
        "   TAG_Long('Time'): 1",
        "   TAG_Long('LastPlayed'): *",
        "   TAG_Int('SpawnX'): 0",
        "   TAG_Int('SpawnY'): 2",
        "   TAG_Int('SpawnZ'): 0",
        "   TAG_Long('SizeOnDisk'): 0",
        "   TAG_Long('RandomSeed'): *",
        "   TAG_Int('version'): 19132",
        "   TAG_String('LevelName'): Testing",
        "   TAG_Compound('Player'): {3 Entries}",
        "   {",
        "       TAG_Int('Score'): 0",
        "       TAG_Int('Dimension'): 0",
        "       TAG_Compound('Inventory'): {0 Entries}",
        "   }",
        "}"
    ]
    def testNBTGeneration(self):
        output = self.runScript('generate_level_dat.py', [])
        self.assertEqual(len(output), 18)
        self.assertEqualString(output[0],  self.expected[0])
        self.assertEqualString(output[10], self.expected[10])
        self.assertEqualString(output[11], self.expected[11])
        self.assertEqualString(output[13], self.expected[13])


class ScoreboardScriptTest(ScriptTestCase):
    """Scoreboard unit test"""

    expected = [
        'soulthps: 0 Diamond',
        'soulthps: 1 Deaths',
        'soulthps: 19238 Time',
        'fwaggle: 77 Diamond',
        'fwaggle: 9 Deaths',
        'fwaggle: 26 Level',
        'fwaggle: 2471784 Time',
        'fwaggle: 1035 Kills',
        'Sabriena: 60 Diamond',
        'Sabriena: 2 Deaths',
        'Sabriena: 4 Level',
        'Sabriena: 1029806 Time',
        'Sabriena: 187 Kills',
        'DuncanDonutz: 22 Diamond',
        'DuncanDonutz: 7 Deaths',
        'DuncanDonutz: 15 Level',
        'DuncanDonutz: 1313860 Time',
        'DuncanDonutz: 30 Kills',
        ]

    def testScoreboard(self):
        output = self.runScript('scoreboard.py', ['tests/world_test',])
        self.assertTrue(len(output) == 18, "Expected output of 18 lines long")
        self.assertEqualOutput(output, self.expected)


# Load resources once.
# Implement as setUpModule/tearDownModule, since it only needs to be called 
# once for the ScriptTestCase class. By default, a setUpClass/tearDownClass 
# calls it for each subclass.

def setUpModule():
    """Download sample world, and copy Anvil and McRegion files to temporary folders."""
    if ScriptTestCase.worldfolder == None:
        downloadsample.install()
        ScriptTestCase.worldfolder = downloadsample.worlddir
    if ScriptTestCase.mcregionfolder == None:
        ScriptTestCase.mcregionfolder = downloadsample.temp_mcregion_world()
    if ScriptTestCase.anvilfolder == None:
        ScriptTestCase.anvilfolder = downloadsample.temp_anvil_world()

def tearDownModule():
    """Remove temporary folders with Anvil and McRegion files."""
    if ScriptTestCase.mcregionfolder != None:
        downloadsample.cleanup_temp_world(ScriptTestCase.mcregionfolder)
    if ScriptTestCase.anvilfolder != None:
        downloadsample.cleanup_temp_world(ScriptTestCase.anvilfolder)
    ScriptTestCase.worldfolder = None
    ScriptTestCase.mcregionfolder = None
    ScriptTestCase.anvilfolder = None


if __name__ == '__main__':
    logger = logging.getLogger("nbt.tests.exampletests")
    if len(logger.handlers) == 0:
        # Logging is not yet configured. Configure it.
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
    unittest.main(verbosity=2, failfast=True)
