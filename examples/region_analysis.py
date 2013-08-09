#!/usr/bin/env python
"""
Defragment a given region file.
"""

import locale, os, sys
import collections
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
	def get_name(self, status):
		if status in self.names:
			return self.names[status]
		else:
			return "Status %s" % status
	def results(self):
		for value in sorted(self.counts.keys()):
			yield value, self.counts[value], self.get_name(value)
	def total(self):
		return sum(self.counts.values())

class ByteCounter(object):
	"""Keep track of types of bytes in a binary stream."""
	def __init__(self):
		self.counts = {}
	def count(self, bytestream):
		if isinstance(bytestream, collections.Iterable):
			for byte in bytestream:
				if byte not in self.counts:
					self.counts[byte] = 0
				self.counts[byte] += 1
		else:
			if bytestream not in self.counts:
				self.counts[bytestream] = 0
			self.counts[bytestream] += 1
	def results(self):
		for value in sorted(self.counts.keys()):
			yield value, self.counts[value]
	

def analyse_regionfile(filename, warnings=True):
	region = RegionFile(filename)
	
	statuscounts = Statuses()
	errors = []
	if region.size % 4096 != 0:
		errors.append("File size is %d bytes, which is not a multiple of 4096" % region.size)
	sectorsize = region.bytes_to_sector(region.size)
	sectors = sectorsize*[None]
	if region.size == 0:
		errors.append("File size is 0 bytes")
		sectors = []
	elif sectorsize < 2:
		errors.append("File size is %d bytes, too small for the 8192 byte header" % region.size)
	else:
		sectors[0] = "locations"
		sectors[1] = "timestamps"
	unusedfirsts = ByteCounter()
	unusedmiddle = ByteCounter()
	unusedend = ByteCounter()
	for x in range(32):
		for z in range(32):
			c = ChunkMetadata(x,z)
			(c.sectorstart, c.sectorlen, c.timestamp, status) = region.header[x,z]
			(c.length, c.compression, c.status) = region.chunk_headers[x,z]
			
			if c.status < 0:
				errors.append("chunk %d,%d has status %d: %s" % \
					(x, z, c.status, statuscounts.get_name(c.status)))
			
			if c.sectorstart != 0:
				if c.sectorlen <= 0:
					errors.append("chunk %d,%d is %d sectors in length" % (x, z, c.sectorlen))
				allocatedbytes = 4096 * c.sectorlen
				requiredsectors = region.bytes_to_sector(c.length + 4)
				if c.length + 4 > allocatedbytes:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d sectors, " \
						"but only %d %s allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, c.sectorlen, \
						"sector is" if (c.sectorlen == 1) else "sectors are"))
				elif c.length + 4 + 4096 == allocatedbytes:
					# If the block fits in exactly n sectors, Minecraft seems to allocated n+1 sectors
					# Threat this as a warning instead of an error.
					if warnings:
						errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d %s, " \
							"but %d sectors are allocated" % \
							(x, z, c.length+4, c.length-1, requiredsectors, \
							"sector" if (requiredsectors == 1) else "sectors", c.sectorlen))
				elif c.sectorlen > requiredsectors:
					errors.append("chunk %d,%d is %d bytes (4+1+%d) and requires %d %s, " \
						"but %d sectors are allocated" % \
						(x, z, c.length+4, c.length-1, requiredsectors, \
						"sector" if (requiredsectors == 1) else "sectors", c.sectorlen))
				
				if warnings:
					# Read the unused bytes in a sector and check if all bytes are zeroed.
					unusedlen = 4096*c.sectorlen - (c.length+4)
					if unusedlen > 0:
						region.file.seek(4096*c.sectorstart + 4 + c.length)
						unused = region.file.read(unusedlen)
						zeroes = unused.count(b'\x00')
						if zeroes < unusedlen:
							errors.append("%d of %d unused bytes are not zeroed in sector %d after chunk %d,%d" % \
								(unusedlen-zeroes, unusedlen, c.sectorstart + c.sectorlen - 1, x, z))
			else:
				# c.sectorstart == 0:
				if c.sectorlen != 0:
					errors.append("chunk %d,%d is not created, but is %d sectors in length" % (x, z, c.sectorlen))
				if c.timestamp != 0:
					errors.append("chunk %d,%d is not created, but has timestamp %d" % (x, z, c.timestamp))
			
			statuscounts.count(c.status)
			for b in range(c.sectorlen):
				m = "chunk %-2d,%-2d part %d/%d" % (x, z, b+1, c.sectorlen)
				p = c.sectorstart + b
				if p > sectorsize:
					errors.append("%s outside file" % (m))
					break
				if sectors[p] != None:
					errors.append("overlap in sector %d: %s and %s" % (p, sectors[p], m))
				sectors[p] = m
	
	e = sectors.count(None)
	if e > 0:
		if warnings:
			errors.append("Fragementation: %d of %d sectors are unused" % (e, sectorsize))
		for sector, content in enumerate(sectors):
			if content == None:
				sectors[sector] = "empty"
				if warnings:
					region.file.seek(4096*sector)
					unused = region.file.read(4096)
					zeroes = unused.count(b'\x00')
					if zeroes < 4096:
						errors.append("%d bytes are not zeroed in unused sector %d" % (4096-zeroes, sector))

	return errors, statuscounts, sectors
	

def debug_regionfile(filename, warnings=True):
	print(filename)
	errors, statuscounts, sectors = analyse_regionfile(filename, warnings)

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

def print_errors(filename, warnings=True):
	print(filename)
	errors, statuscounts, sectors = analyse_regionfile(filename, warnings)
	for error in errors:
		print(error)



if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-v", "--verbose", dest="verbose", default=False,
					action="store_true", help="Show detailed info about region file")
	parser.add_option("-q", "--quiet", dest="warnings", default=True,
					action="store_false", help="Only show errors, no warnings")

	(options, args) = parser.parse_args()
	if (len(args) == 0):
		print("No region file specified! Use -v for verbose results; -q for errors only (no warnings)")
		sys.exit(64) # EX_USAGE

	for filename in args:
		try:
			if options.verbose:
				debug_regionfile(filename, options.warnings)
			else:
				print_errors(filename, options.warnings)
		except IOError as e:
			sys.stderr.write("%s: %s\n" % (e.filename, e.strerror))
			# sys.exit(72) # EX_IOERR
	sys.exit(0)