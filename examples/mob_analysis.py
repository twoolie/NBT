#!/usr/bin/env python

import locale, os, sys

# local module
try:
    import nbt
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(sys.path[0],os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
from nbt.region import RegionFile
from nbt.chunk import Chunk

class Position(object):
	def __init__(self, x,y,z):
		self.x  = x
		self.y  = y
		self.z  = z

class Entity(object):
	def __init__(self, type, pos):
		self.type  = type
		self.pos   = Position(*pos)


def entities_per_chunk(chunk):
	"""Given a chunk, find all entities (mobs, items, vehicles)"""
	entities = []
	for entity in chunk['Entities']:
		x,y,z = entity["Pos"]
		entities.append(Entity(entity["id"].value, (x.value,y.value,z.value)))
	return entities

def process_region_file(filename):
	"""Given a region filename, return the number of blocks of each ID in that file"""
	entities = []
	file = RegionFile(filename)
	
	# Get all chunks
	chunks = file.get_chunks()
	print "Parsing",os.path.basename(filename),"...",len(chunks),"chunks"
	entities = []
	for cc in chunks:
		chunk = file.get_chunk(cc['x'], cc['z'])
		leveldata = chunk['Level']
		# chunk = Chunk(c)
		entities.extend(entities_per_chunk(leveldata))
	
	return entities


def print_results(entities):
	locale.setlocale(locale.LC_ALL, 'en_US')
	for entity in entities:
		print "%s at %s,%s,%s" % \
			(entity.type,\
			locale.format("%0.1f",entity.pos.x,grouping=True),\
			locale.format("%0.1f",entity.pos.y,grouping=True),\
			locale.format("%0.1f",entity.pos.z,grouping=True))


def main(world_folder):
	regions = os.listdir(os.path.join(world_folder,'region'))
	
	try:
		for filename in regions:
			entities = process_region_file(os.path.join(world_folder,'region',filename))
			print_results(entities)
	
	except KeyboardInterrupt:
		return 4 # EINTR
	return 0 # NOERR


if __name__ == '__main__':
	if (len(sys.argv) == 1):
		print "No world folder specified!"
		sys.exit(22) # EINVAL
	world_folder = sys.argv[1]
	if (not os.path.exists(world_folder)):
		print "No such folder as "+filename
		sys.exit(2) # ENOENT
	
	sys.exit(main(world_folder))
