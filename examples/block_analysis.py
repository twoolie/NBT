#!/usr/bin/env python
"""
Finds the contents of the different blocks in a level, taking different data values (sub block types) into account.
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

def stats_per_chunk(chunk, block_data_totals):
	"""Given a chunk, increment the block types with the number of blocks found"""
	for block_id, data_id in chunk.blocks.get_all_blocks_and_data():
		block_data_totals[block_id][data_id] += 1

def bounded_stats_per_chunk(chunk, block_data_totals, start, stop):
	"""Given a chunk, return the number of blocks types within the specified selection"""
	chunk_z, chunk_x = chunk.get_coords()
	for z in range(16):
		world_z = z + chunk_z*16
		if ( (start != None and world_z < int(start[2])) or (stop != None and  world_z > int(stop[2])) ):
			# Outside the bounding box; skip to next iteration
			#print "Z break:",world_z,start[2],stop[2]
			break
		for x in range(16):
			world_x = x + chunk_x*16
			if ( (start != None and world_x < int(start[0])) or (stop != None and world_x > int(stop[0])) ):
				# Outside the bounding box; skip to next iteration
				#print "X break:",world_x,start[0],stop[0]
				break
			for y in range(128):
				if ( (start != None and y < int(start[1])) or (stop != None and y > int(stop[1])) ):
					# Outside the bounding box; skip to next iteration
					#print "Y break:",y,start[1],stop[1]
					break
				
				#print "Chunk:",c['x'], c['z'],"Coord:",x,y,z
				block_id,block_data = chunk.blocks.get_block_and_data(x,y,z)
				block_data_totals[block_id][block_data] += 1

def process_region_file(filename, start, stop):
	"""Given a region filename, return the number of blocks of each ID in that file"""
	pieces = filename.split('.')
	rx = int(pieces[1])
	rz = int(pieces[2])
	
	block_data_totals = [[0]*16 for i in xrange(256)] # up to 16 data numbers in 256 block IDs
	
	# Does the region overlap the bounding box at all?
	if (start != None):
		if ( (rx+1)*512-1 < int(start[0]) or (rz+1)*512-1 < int(start[2]) ):
			return block_data_totals
	elif (stop != None):
		if ( rx*512-1 > int(stop[0]) or rz*512-1 > int(stop[2]) ):
			return block_data_totals
	
	file = RegionFile(filename)
	
	# Get all chunks
	chunks = file.get_chunks()
	print "Parsing",os.path.basename(filename),"...",len(chunks),"chunks"
	for c in chunks:
		# Does the chunk overlap the bounding box at all?
		if (start != None):
			if ( (c['x']+1)*16 + rx*512 - 1 < int(start[0]) or (c['z']+1)*16 + rz*512 - 1 < int(start[2]) ):
				continue
		elif (stop != None):
			if ( c['x']*16 + rx*512 - 1 > int(stop[0]) or c['z']*16 + rz*512 - 1 > int(stop[2]) ):
				continue
		
		chunk = Chunk(file.get_chunk(c['x'], c['z']))
		assert chunk.get_coords() == (c['x'] + rx*32, c['z'] + rz*32)
		#print "Parsing chunk ("+str(c['x'])+", "+str(c['z'])+")"
		# Parse the blocks

		# Fast code if no start or stop coordinates are specified
		# TODO: also use this code if start/stop is specified, but the complete chunk is included
		if (start == None and stop == None):
			stats_per_chunk(chunk, block_data_totals)
		else:
			# Slow code that iterates through each coordinate
			bounded_stats_per_chunk(chunk, block_data_totals, start, stop)
	
	return block_data_totals


def print_results(block_data_totals):
	locale.setlocale(locale.LC_ALL, 'en_US')
	
	# Analyze blocks
	for block_id,data in enumerate(block_data_totals):
		if sum(data) > 0:
			datastr = ", ".join([locale.format_string("%d: %d", (i,c), grouping=True) for (i,c) in enumerate(data) if c > 0])
			print locale.format_string("block id %3d: %12d (data id %s)", (block_id,sum(data),datastr), grouping=True)
	block_totals = [sum(data_totals) for data_totals in block_data_totals]
	
	total_blocks = sum(block_totals)
	solid_blocks = total_blocks - block_totals[0]
	solid_ratio = (solid_blocks+0.0)/total_blocks if (total_blocks > 0) else 0
	print locale.format("%d", total_blocks, grouping=True),'total blocks in region,',locale.format("%d", solid_blocks, grouping=True),"are solid ({0:0.4%})".format(solid_ratio)
	
	# Find valuable blocks
	print 'Diamond Ore:', locale.format("%d", block_totals[56], grouping=True)
	print 'Gold Ore:', locale.format("%d", block_totals[14], grouping=True)
	print 'Redstone Ore:', locale.format("%d", block_totals[73], grouping=True)
	print 'Iron Ore:', locale.format("%d", block_totals[15], grouping=True)
	print 'Coal Ore:', locale.format("%d", block_totals[16], grouping=True)
	print 'Lapis Lazuli Ore:', locale.format("%d", block_totals[21], grouping=True)
	print 'Dungeons:', locale.format("%d", block_totals[52], grouping=True)
	
	print 'Clay:', locale.format("%d", block_totals[82], grouping=True)
	print 'Sugar Cane:', locale.format("%d", block_totals[83], grouping=True)
	print 'Cacti:', locale.format("%d", block_totals[81], grouping=True)
	print 'Pumpkin:', locale.format("%d", block_totals[86], grouping=True)
	print 'Dandelion:', locale.format("%d", block_totals[37], grouping=True)
	print 'Rose:', locale.format("%d", block_totals[38], grouping=True)
	print 'Brown Mushroom:', locale.format("%d", block_totals[39], grouping=True)
	print 'Red Mushroom:', locale.format("%d", block_totals[40], grouping=True)
	print 'Lava Springs:', locale.format("%d", block_totals[11], grouping=True)
	


def main(world_folder, start=None, stop=None):
	if (not os.path.exists(world_folder)):
		print "No such folder as "+filename
		return 2 # ENOENT
	
	regions = glob.glob(os.path.join(world_folder,'region','*.mcr'))
	
	block_data_totals = [[0]*16 for i in xrange(256)] # up to 16 data numbers in 256 block IDs
	try:
		for filename in regions:
			region_totals = process_region_file(os.path.join(world_folder,'region',filename), start, stop)
			for i, data in enumerate(region_totals):
				for j, total in enumerate(data):
					block_data_totals[i][j] += total
	
	except KeyboardInterrupt:
		print_results(block_data_totals)
		return 4 # EINTR
	
	print_results(block_data_totals)
	return 0 # EX_OK


if __name__ == '__main__':
	if (len(sys.argv) == 1):
		print "No world folder specified!"
		sys.exit(22) # EINVAL
	world_folder = sys.argv[1]
	start,stop = None,None
	if (len(sys.argv) == 4):
		# A min/max corner was specified
		start_str = sys.argv[2][1:-1] # Strip parenthesis...
		start = tuple(start_str.split(',')) # and convert to tuple
		stop_str = sys.argv[3][1:-1] # Strip parenthesis...
		stop = tuple(stop_str.split(',')) # and convert to tuple
	
	sys.exit(main(world_folder, start, stop))
