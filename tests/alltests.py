#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import logging

testmodules = ['examplestests', 'nbttests']
"""Files to check for test cases. Do not include the .py extension."""


def get_testsuites_in_module(module):
	"""
	Return a list of unittest.TestSuite subclasses defined in module.
	"""
	suites = []
	for name in dir(module):
		obj = getattr(module, name)
		if isinstance(obj, type) and issubclass(obj, unittest.TestSuite):
			suites.append(obj)
	return suites


def load_tests_in_modules(modulenames):
	"""
	Given a list of module names, import the modules, load and run the 
	test cases in these modules. The modules are typically files in the 
	current directory, but this is not a requirement.
	"""
	loader = unittest.TestLoader()
	suites = []
	for name in modulenames:
		module = __import__(name)
		suite = loader.loadTestsFromModule(module)
		for suiteclass in get_testsuites_in_module(module):
			# Wrap suite in TestSuite classes
			suite = suiteclass(suite)
		suites.append(suite)
	suite = unittest.TestSuite(suites)
	return suite



if __name__ == "__main__":
	logger = logging.getLogger("nbt.tests")
	if len(logger.handlers) == 0:
		# Logging is not yet configured. Configure it.
		logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
	testresult = unittest.TextTestRunner(verbosity=2).run(load_tests_in_modules(testmodules))
	sys.exit(not testresult.wasSuccessful())
