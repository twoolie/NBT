#!/usr/bin/env python
"""
Finds and prints the contents of chests (including minecart chests)
"""
import locale, os, sys
import glob
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
		self.x = x
		self.y = y
		self.z = z

class Chest(object):
	def __init__(self, type, pos, items):
		self.type  = type
		self.pos   = Position(*pos)
		self.items = items

def items_from_nbt(nbtlist):
	items = {}	# block_id -> count
	for item in nbtlist:
		id = item['id'].value
		count = item['Count'].value
		if id not in items:
			items[id] = 0
		items[id] += count
	return items

def chests_per_chunk(chunk):
	"""Given a chunk, increment the block types with the number of blocks found"""
	# if (len(chunk['Entities']) > 0) or (len(chunk['TileEntities']) > 0):
	#	print "Chunk ", chunk["xPos"],chunk["zPos"]
	entities = []
	for entity in chunk['Entities']:
		if entity["id"].value == "Minecart" and entity["type"].value == 1:
			x,y,z = entity["Pos"]
			x,y,z = x.value,y,value,z.value
			items = items_from_nbt(entity["Items"])
			entities.append(Chest("Minecart with chest",(x,y,z),items))
	for entity in chunk['TileEntities']:
		if entity["id"].value == "Chest":
			x,y,z = entity["x"].value,entity["y"].value,entity["z"].value
			items = items_from_nbt(entity["Items"])
			entities.append(Chest("Chest",(x,y,z),items))
	return entities

def process_region_file(filename):
	"""Given a region filename, return the number of blocks of each ID in that file"""
	chests = []
	file = RegionFile(filename)
	
	# Get all chunks
	chunks = file.get_chunks()
	print "Parsing",os.path.basename(filename),"...",len(chunks),"chunks"
	for cc in chunks:
		chunk = file.get_chunk(cc['x'], cc['z'])
		leveldata = chunk['Level']
		chests.extend(chests_per_chunk(leveldata))
	
	return chests


def print_results(chests):
	locale.setlocale(locale.LC_ALL, 'en_US')
	for chest in chests:
		itemcount = sum(chest.items.values())
		print "%s at %s,%s,%s with %d items:" % \
			(chest.type,\
			locale.format("%0.1f",chest.pos.x,grouping=True),\
			locale.format("%0.1f",chest.pos.y,grouping=True),\
			locale.format("%0.1f",chest.pos.z,grouping=True),\
			itemcount)
		for blockid,count in chest.items.items():
			print "   %3dx Item %d" % (count, blockid)


def main(world_folder):
	regions = glob.glob(os.path.join(world_folder,'region','*.mcr'))
	
	try:
		for filename in regions:
			chests = process_region_file(os.path.join(world_folder,'region',filename))
			print_results(chests)
	
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
