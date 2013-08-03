#!/usr/bin/env python
"""
Defragment a given region file.
"""

import locale, os, sys
from optparse import OptionParser

# local module
try:
	import nbt
except ImportError:
	# nbt not in search path. Let's see if it can be found in the parent folder
	extrasearchpath = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
	if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
		raise
	sys.path.append(extrasearchpath)
from nbt.region import RegionFile


class ChunkMetadata(object):
	def __init__(self, x, z):
		self.x = x
		self.z = z
		self.sectorstart = None
		self.sectorlen = None
		self.timestamp = None
		self.length = None
		self.compression = None
		self.status = None
	def __repr__(self):
		return "chunk %02s,%02s  [%d]  @%-5d %2d  %-5s %-5s %d" % (self.x, self.z, self.status, self.sectorstart, self.sectorlen, self.length, self.compression, self.timestamp)


class Statuses(object):
	"""Keep track of the number of statuses for all chunks.
	The different types of status are defined in RegionFile"""
	def __init__(self):
		self.counts = {}
		self.names = {}
		for var in dir(RegionFile):
			if var.startswith("STATUS_CHUNK_"):
				name = var[13:].title().replace("_"," ")
				value = getattr(RegionFile, var)
				self.counts[value] = 0
				self.names[value] = name
	def count(self, status, count=1):
		if status not in self.counts:
			self.counts[status] = 0
			self.names = "Status %s" % status
		self.counts[status] += count
	def results(self):
		for value in sorted(self.counts.keys()):
			yield value, self.counts[value], self.names[value]
	def total(self):
		return sum(self.counts.values())

def analyse_regionfile(filename):
	region = RegionFile(filename)
	
	statuscounts = Statuses()
	errors = []
	if region.size % 4096 != 0:
		errors.append("File size is %d bytes, which is not a multiple of 4096" % region.size)
	sectorsize = region.bytes_to_sector(region.size)
	sectors = sectorsize*["empty"]
	sectors[0] = "locations"
	sectors[1] = "timestamps"
	for x in range(32):
		for z in range(32):
			c = ChunkMetadata(x,z)
			(c.sectorstart, c.sectorlen, c.timestamp, status) = region.header[x,z]
			(c.length, c.compression, c.status) = region.chunk_headers[x,z]
			
			if c.status < 0:
				errors.append("chunk %d,%d has status %d: %s" % \
					(x, z, c.status, statuscounts.names[c.status]))
			
			if c.sectorstart != 0:
				if c.sectorlen == 0:
					errors.append("chunk %d,%d is 0 sectors in length" % (x, z))
				requiredsectors = region.bytes_to_sector(c.length + 4)
				if c.sectorlen < requiredsectors:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d sectors, " \
						"but only %d sectors are allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, c.sectorlen))
				elif c.sectorlen > requiredsectors:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d sectors, " \
						"but %d sectors are allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, c.sectorlen))
				# The following are not errors, but merely notes for myself to check if the 
				# sector lenght calculation is correct.
				elif c.length + 4 == c.sectorlen * 4096:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d sector(s), " \
						"and indeed %d sector(s) is/are allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, c.sectorlen))
				elif c.length + 5 == c.sectorlen * 4096:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d sector(s), " \
						"and indeed %d sector(s) is/are allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, c.sectorlen))
				elif c.length + 6 == c.sectorlen * 4096:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d sector(s), " \
						"and indeed %d sector(s) is/are allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, c.sectorlen))
			
			statuscounts.count(c.status)
			for b in range(c.sectorlen):
				m = "chunk %-2s,%-2s part %d/%d" % (x, z, b+1, c.sectorlen)
				p = c.sectorstart + b
				if p > sectorsize:
					errors.append("%s outside file" % (m))
					break
				if sectors[p] != "empty":
					errors.append("overlap in sector %d: %s and %s" % (p, sectors[p], m))
				sectors[p] = m
	
	e = sectors.count("empty")
	if e > 0:
		errors.append("Fragementation: File has %d unused sectors" % e)

	return errors, statuscounts, sectors
	

def debug_regionfile(filename):
	print(filename)
	errors, statuscounts, sectors = analyse_regionfile(filename)

	print("File size is %d sectors" % (len(sectors)))
	print("Chunk statuses:")
	for value, count, name in statuscounts.results():
		print("status %2d %-21s%4d chunks" % (value, ("(%s):" % name), count))
	print("%d chunks in total" % statuscounts.total()) #q should be 1024

	if len(errors) > 0:
		print("Errors:")
	else:
		print("No errors or warnings found")
	for error in errors:
		print(error)

	print("File content by sector:")
	for i,s in enumerate(sectors):
		print("sector %03d: %s" % (i, s))

def print_errors(filename):
	print(filename)
	errors, statuscounts, sectors = analyse_regionfile(filename)
	for error in errors:
		print(error)



if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-v", "--verbose", dest="verbose", default=False,
					action="store_true", help="Show detailed info about region file")

	(options, args) = parser.parse_args()
	if (len(args) == 0):
		print("No region file specified! Use -v for verbose results.")
		sys.exit(64) # EX_USAGE

	for filename in args:
		try:
			if options.verbose:
				debug_regionfile(filename)
			else:
				print_errors(filename)
		except IOError as e:
			sys.stderr.write("%s: %s\n" % (e.filename, e.strerror))
			# sys.exit(72) # EX_IOERR
	sys.exit(0)
