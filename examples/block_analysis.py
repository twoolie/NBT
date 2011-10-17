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

if (len(sys.argv) == 1):
	print "No world folder specified!"
	sys.exit()

world_folder = sys.argv[1]
if (not os.path.exists(world_folder)):
	print "No such folder as "+filename
	sys.exit()

if (world_folder[-1] == '/'):
	world_folder = world_folder[:-1] # Trim trailing slash

regions = os.listdir(world_folder+'/region/')

start = None
stop = None
if (len(sys.argv) == 4):
	# A min/max corner was specified
	start_str = sys.argv[2][1:-1] # Strip parenthesis...
	start = tuple(start_str.split(',')) # and convert to tuple
	stop_str = sys.argv[3][1:-1] # Strip parenthesis...
	stop = tuple(stop_str.split(',')) # and convert to tuple

block_totals = [0]*255 # up to 255 block types
try:
	for filename in regions:
		print "Parsing",filename,"..."
		pieces = filename.split('.')
		rx = int(pieces[1])
		rz = int(pieces[2])
		
		# Does the region overlap the bounding box at all?
		if (start != None):
			if ( (rx+1)*512-1 < int(start[0]) or (rz+1)*512-1 < int(start[2]) ):
				continue
		elif (stop != None):
			if ( rx*512-1 > int(stop[0]) or rz*512-1 > int(stop[2]) ):
				continue
				
		file = RegionFile(filename=world_folder+'/region/'+filename)
		
		# Get all chunks
		chunks = file.get_chunks()
		for c in chunks:
			# Does the chunk overlap the bounding box at all?
			if (start != None):
				if ( (c['x']+1)*16 + rx*512 - 1 < int(start[0]) or (c['z']+1)*16 + rz*512 - 1 < int(start[2]) ):
					continue
			elif (stop != None):
				if ( c['x']*16 + rx*512 - 1 > int(stop[0]) or c['z']*16 + rz*512 - 1 > int(stop[2]) ):
					continue
			
			chunk = Chunk(file.get_chunk(c['x'], c['z']))
			#print "Parsing chunk ("+str(c['x'])+", "+str(c['z'])+")"
			
			# Parse the blocks

			# Fast code if no start or stop coordinates are specified
			# TODO: also use this code if start/stop is specified, but the complete chunk is included
			if (start == None and stop == None):
				for block_id in chunk.blocks.get_all_blocks():
					block_totals[block_id] += 1
				continue
			
			# Slow code that iterates through each coordinate
			for z in range(16):
				world_z = z + c['z']*16 + rz*512
				if ( (start != None and world_z < int(start[2])) or (stop != None and  world_z > int(stop[2])) ):
					# Outside the bounding box; skip to next iteration
					#print "Z break:",world_z,start[2],stop[2]
					break
				for x in range(16):
					world_x = x + c['x']*16 + rx*512
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
						block_id = chunk.blocks.get_block(x,y,z)
						block_totals[block_id] += 1
except KeyboardInterrupt:
	print block_totals
	raise

print block_totals

# Analyze blocks
locale.setlocale(locale.LC_ALL, 'en_US')

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

