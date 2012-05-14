#!/usr/bin/env python
"""
Finds and prints the contents of chests (including minecart chests)
"""
import locale
import os
import sys

# local module
try:
	import nbt
except ImportError:
	# nbt not in search path. Let's see if it can be found in the parent folder
	extrasearchpath = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir))
	if not os.path.exists(os.path.join(extrasearchpath, 'nbt')):
		raise
	sys.path.append(extrasearchpath)
from nbt.world import WorldFolder


class Position(object):
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z


class Chest(object):
	def __init__(self, type, pos, items):
		self.type = type
		self.pos = Position(*pos)
		self.items = items


def items_from_nbt(nbtlist):
	items = {}  # block_id -> count
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
	#	print("Chunk %d,%d" % (chunk["xPos"],chunk["zPos"]))
	entities = []
	for entity in chunk['Entities']:
		if entity["id"].value == "Minecart" and entity["type"].value == 1:
			x, y, z = entity["Pos"]
			x, y, z = x.value, y.value, z.value
			items = items_from_nbt(entity["Items"])
			entities.append(Chest("Minecart with chest", (x, y, z), items))
	for entity in chunk['TileEntities']:
		if entity["id"].value == "Chest":
			x, y, z = entity["x"].value, entity["y"].value, entity["z"].value
			items = items_from_nbt(entity["Items"])
			entities.append(Chest("Chest", (x, y, z), items))
	return entities


def print_results(chests):
	locale.setlocale(locale.LC_ALL, '')
	for chest in chests:
		itemcount = sum(chest.items.values())
		print("%s at %s,%s,%s with %d items:" % \
			(chest.type,\
			locale.format("%0.1f", chest.pos.x, grouping=True),\
			locale.format("%0.1f", chest.pos.y, grouping=True),\
			locale.format("%0.1f", chest.pos.z, grouping=True),\
			itemcount))
		for blockid, count in chest.items.items():
			print("   %3dx Item %d" % (count, blockid))


def main(world_folder):
	world = WorldFolder(world_folder)

	try:
		for chunk in world.iter_nbt():
			print_results(chests_per_chunk(chunk["Level"]))

	except KeyboardInterrupt:
		return 75  # EX_TEMPFAIL

	return 0  # NOERR


if __name__ == '__main__':
	if (len(sys.argv) == 1):
		print("No world folder specified!")
		sys.exit(64)  # EX_USAGE
	world_folder = sys.argv[1]
	if (not os.path.exists(world_folder)):
		print("No such folder as " + world_folder)
		sys.exit(72)  # EX_IOERR

	sys.exit(main(world_folder))
