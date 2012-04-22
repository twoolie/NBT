#!/usr/bin/env python
# encoding: utf-8
"""
Run all scripts in examples on specific sample world.
"""

import sys
import os
# import logging
import unittest
import subprocess
import shutil
import tempfile
import glob
# local modules
import downloadsample

try:
	from unittest import skipIf
except ImportError:
	# Support for Python 2.6
	def skipIf(condition, message):
		def decorator(f):
			return None if condition else f
		return decorator


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
	@classmethod
	def installsampleworld(cls):
		downloadsample.install()
		cls.worldfolder = downloadsample.worlddir
	@classmethod
	def extractMcRegionWorld(cls):
		cls.mcregionfolder = tempfile.mkdtemp(prefix="nbtmcregion")
		_mkdir(cls.mcregionfolder, 'region')
		_copyglob(cls.worldfolder, cls.mcregionfolder, "region/*.mcr")
		_copyrename(cls.worldfolder, cls.mcregionfolder, "level.dat_mcr", "level.dat")
	@classmethod
	def extractAnvilWorld(cls):
		"""Download and extract a sample world (if not available), and copy the anvil-specific files to a temporary directory."""
		cls.anvilfolder = tempfile.mkdtemp(prefix="nbtanvil")
		_mkdir(cls.anvilfolder, 'region')
		_copyglob(cls.worldfolder, cls.anvilfolder, "region/*.mca")
		_copyrename(cls.worldfolder, cls.anvilfolder, "level.dat", "level.dat")
	@classmethod
	def setUpClass(cls):
		pass
	@classmethod
	def tearDownClass(cls):
		if cls.mcregionfolder:
			shutil.rmtree(cls.mcregionfolder, ignore_errors=True)
			cls.mcregionfolder = None
		if cls.anvilfolder:
			shutil.rmtree(cls.anvilfolder, ignore_errors=True)
			cls.anvilfolder = None
	def runScript(self, script, args):
		script = os.path.join(self.examplesdir, script)
		args.insert(0, script)
		p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		p.wait()
		self.assertEqual(p.returncode, 0, "return code is %d" % p.returncode)
		r = p.stdout.readlines()
		p.stdout.close()
		return r
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
	# 	cls.installsampleworld()
	# 	cls.extractAnvilWorld()
	# def testAnvilWorld(self):
	# 	output = self.runScript('biome_analysis.py', [self.anvilfolder])

class BlockAnalysisScriptTest(ScriptTestCase):
	expected = [
		"DiamondOre:1743",
		"GoldOre:4838",
		"RedstoneOre:14487",
		"IronOre:52906",
		"CoalOre:97597",
		"LapisLazuliOre:2051",
		"Dungeons:26",
		"Clay:897",
		"SugarCane:22",
		"Cacti:0",
		"Pumpkin:6",
		"Dandelion:513",
		"Rose:131",
		"BrownMushroom:40",
		"RedMushroom:31",
		"LavaSprings:47665",
	]
	@classmethod
	def setUpClass(cls):
		cls.installsampleworld()
		cls.extractMcRegionWorld()
		# cls.extractAnvilWorld()
	def testMcRegionWorld(self):
		output = self.runScript('block_analysis.py', [self.mcregionfolder])
		self.assertTrue(len(output) >= 73, "Expected output of at least 73 lines long")
		output = [l.translate(None," ,.") for l in output[-16:]]
		self.assertEqualOutput(output, self.expected)
	# TODO: Anvil does not yet work.
	# def testAnvilWorld(self):
	# 	output = self.runScript('block_analysis.py', [self.anvilfolder])
	# 	print repr(output)
	# 	self.assertTrue(len(output) >= 73, "Expected output of at least 73 lines long")
	# 	output = [l.translate(None," ,.") for l in output[-16:]]
	# 	self.assertEqualOutput(output, self.expected)

class ChestAnalysisScriptTest(ScriptTestCase):
	@classmethod
	def setUpClass(cls):
		cls.installsampleworld()
		cls.extractMcRegionWorld()
		cls.extractAnvilWorld()
	def testMcRegionWorld(self):
		output = self.runScript('chest_analysis.py', [self.mcregionfolder])
		self.assertEqual(len(output), 178)
		count = len(filter(lambda l: l.startswith('Chest at '), output))
		self.assertEqual(count, 38)
	def testAnvilWorld(self):
		output = self.runScript('chest_analysis.py', [self.anvilfolder])
		self.assertEqual(len(output), 178)
		count = len(filter(lambda l: l.startswith('Chest at '), output))
		self.assertEqual(count, 38)

class MapScriptTest(ScriptTestCase):
	@classmethod
	def setUpClass(cls):
		cls.installsampleworld()
		cls.extractMcRegionWorld()
		# cls.extractAnvilWorld()
	@skipIf(sys.version_info[0] >= 3, "PIL library not yet available for Python 3")
	def testMcRegionWorld(self):
		output = self.runScript('map.py', ['--noshow', self.mcregionfolder])
		self.assertTrue(output[-1].startswith("Saved map as "))
	# TODO: this currently writes the map to tests/nbtmcregion*.png files. 
	# The locations should be a tempfile, and the file should be deleted afterwards.
	
	# @skipIf(sys.version_info[0] >= 3, "PIL library not yet available for Python 3")
	# def testAnvilWorld(self):
	# 	output = self.runScript('map.py', ['--noshow', self.anvilfolder])
	# 	self.assertEqualString(output[-1], "Saved map as Sample World.png")

class MobAnalysisScriptTest(ScriptTestCase):
	@classmethod
	def setUpClass(cls):
		cls.installsampleworld()
		cls.extractMcRegionWorld()
		cls.extractAnvilWorld()
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
	@classmethod
	def setUpClass(cls):
		cls.installsampleworld()
		cls.extractMcRegionWorld()
		cls.extractAnvilWorld()
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
		"	TAG_Long('Time'): 1",
		"	TAG_Long('LastPlayed'): *",
		"	TAG_Int('SpawnX'): 0",
		"	TAG_Int('SpawnY'): 2",
		"	TAG_Int('SpawnZ'): 0",
		"	TAG_Long('SizeOnDisk'): 0",
		"	TAG_Long('RandomSeed'): *",
		"	TAG_Int('version'): 19132",
		"	TAG_String('LevelName'): Testing",
		"	TAG_Compound('Player'): {3 Entries}",
		"	{",
		"		TAG_Int('Score'): 0",
		"		TAG_Int('Dimension'): 0",
		"		TAG_Compound('Inventory'): {0 Entries}",
		"	}",
		"}"
	]
	def testNBTGeneration(self):
		output = self.runScript('generate_level_dat.py', [])
		self.assertEqual(len(output), 18)
		self.assertEqualString(output[0],  self.expected[0])
		self.assertEqualString(output[10], self.expected[10])
		self.assertEqualString(output[11], self.expected[11])
		self.assertEqualString(output[13], self.expected[13])




if __name__ == '__main__':
	unittest.main(verbosity=4, failfast=True)
