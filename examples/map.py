#!/usr/bin/env python
"""
Prints a map of the entire world.
"""

import locale, os, sys
import re, math
from struct import pack, unpack
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
from nbt.chunk import Chunk, BlockArray
from nbt.world import WorldFolder,McRegionWorldFolder, AnvilWorldFolder
# PIL module (not build-in)
try:
	from PIL import Image
except ImportError:
	# PIL not in search path. Let's see if it can be found in the parent folder
	sys.stderr.write("Module PIL/Image not found. PIL can be found at http://www.pythonware.com/library/pil/")
	sys.exit(70) # EX_SOFTWARE

def get_heightmap_image(chunk, buffer=False, gmin=False, gmax=False):
	points = chunk.blocks.generate_heightmap(buffer, True)
	# Normalize the points
	hmin = min(points) if (gmin == False) else gmin # Allow setting the min/max explicitly, in case this is part of a bigger map
	hmax = max(points) if (gmax == False) else gmax
	hdelta = hmax-hmin+0.0
	pixels = ""
	for y in range(16):
		for x in range(16):
			# pix X => mc -Z
			# pix Y => mc X
			offset = (15-x)*16+y
			height = int((points[offset]-hmin)/hdelta*255)
			if (height < 0): height = 0
			if (height > 255): height = 255
			pixels += pack(">B", height)
	im = Image.fromstring('L', (16,16), pixels)
	return im

def get_map(chunk):
	# Show an image of the chunk from above
	pixels = ""
	block_colors = {
		0: {'h':0, 's':0, 'l':0},       # Air
		1: {'h':0, 's':0, 'l':32},      # Stone
		2: {'h':94, 's':42, 'l':32},    # Grass
		3: {'h':27, 's':51, 'l':15},    # Dirt
		4: {'h':0, 's':0, 'l':25},      # Cobblestone
		8: {'h':228, 's':50, 'l':23},   # Water
		9: {'h':228, 's':50, 'l':23},   # Water
		10: {'h':16, 's':100, 'l':48},  # Lava
		11: {'h':16, 's':100, 'l':48},  # Lava
		12: {'h':53, 's':22, 'l':58},   # Sand
		13: {'h':21, 's':18, 'l':20},   # Gravel
		17: {'h':35, 's':93, 'l':15},   # Wood
		18: {'h':114, 's':64, 'l':22},  # Leaves
		24: {'h':48, 's':31, 'l':40},   # Sandstone
		37: {'h':60, 's':100, 'l':60},  # Yellow Flower
		38: {'h':0, 's':100, 'l':50},   # Red Flower
		50: {'h':60, 's':100, 'l':50},  # Torch
		51: {'h':55, 's':100, 'l':50},  # Fire
		59: {'h':123, 's':60, 'l':50},  # Crops
		60: {'h':35, 's':93, 'l':15},   # Farmland
		78: {'h':240, 's':10, 'l':85},  # Snow
		79: {'h':240, 's':10, 'l':95},  # Ice
		81: {'h':126, 's':61, 'l':20},  # Cacti
		82: {'h':7, 's':62, 'l':23},    # Clay
		83: {'h':123, 's':70, 'l':50},  # Sugarcane
		86: {'h':24, 's':100, 'l':45},  # Pumpkin
		91: {'h':24, 's':100, 'l':45},  # Jack-o-lantern
	}
	for z in range(16):
		for x in range(16):
			# Find the highest block in this column
			ground_height = 127
			tints = []
			for y in range(127,-1,-1):
				block_id = chunk.blocks.get_block(x,y,z)
				block_data = chunk.blocks.get_data(x,y,z)
				if (block_id == 8 or block_id == 9):
					tints.append({'h':228, 's':50, 'l':23}) # Water
				elif (block_id == 18):
					if (block_data == 1):
						tints.append({'h':114, 's':64, 'l':22}) # Redwood Leaves
					elif (block_data == 2):
						tints.append({'h':93, 's':39, 'l':10}) # Birch Leaves
					else:
						tints.append({'h':114, 's':64, 'l':22}) # Normal Leaves
				elif (block_id == 79):
					tints.append({'h':240, 's':5, 'l':95}) # Ice
				elif (block_id == 51):
					tints.append({'h':55, 's':100, 'l':50}) # Fire
				elif (block_id != 0 or y == 0):
					# Here is ground level
					ground_height = y
					break

			color = block_colors[block_id] if (block_id in block_colors) else {'h':0, 's':0, 'l':100}
			height_shift = (ground_height-64)*0.25
			
			final_color = {'h':color['h'], 's':color['s'], 'l':color['l']+height_shift}
			if final_color['l'] > 100: final_color['l'] = 100
			if final_color['l'] < 0: final_color['l'] = 0
			
			# Apply tints from translucent blocks
			for tint in reversed(tints):
				final_color = hsl_slide(final_color, tint, 0.4)

			rgb = hsl2rgb(final_color['h'], final_color['s'], final_color['l'])

			pixels += pack("BBB", rgb[0], rgb[1], rgb[2])
	im = Image.fromstring('RGB', (16,16), pixels)
	return im


## Color functions for map generation ##

# Hue given in degrees,
# saturation and lightness given either in range 0-1 or 0-100 and returned in kind
def hsl_slide(hsl1, hsl2, ratio):
	if (abs(hsl2['h'] - hsl1['h']) > 180):
		if (hsl1['h'] > hsl2['h']):
			hsl1['h'] -= 360
		else:
			hsl1['h'] += 360
	
	# Find location of two colors on the H/S color circle
	p1x = math.cos(math.radians(hsl1['h']))*hsl1['s']
	p1y = math.sin(math.radians(hsl1['h']))*hsl1['s']
	p2x = math.cos(math.radians(hsl2['h']))*hsl2['s']
	p2y = math.sin(math.radians(hsl2['h']))*hsl2['s']
	
	# Slide part of the way from tint to base color
	avg_x = p1x + ratio*(p2x-p1x)
	avg_y = p1y + ratio*(p2y-p1y)
	avg_h = math.atan(avg_y/avg_x)
	avg_s = avg_y/math.sin(avg_h)
	avg_l = hsl1['l'] + ratio*(hsl2['l']-hsl1['l'])
	avg_h = math.degrees(avg_h)
	
	#print('tint: %s base: %s avg: %s %s %s' % (tint,final_color,avg_h,avg_s,avg_l))
	return {'h':avg_h, 's':avg_s, 'l':avg_l}


# From http://www.easyrgb.com/index.php?X=MATH&H=19#text19
def hsl2rgb(H,S,L):
	H = H/360.0
	S = S/100.0 # Turn into a percentage
	L = L/100.0
	if (S == 0):
		return (int(L*255), int(L*255), int(L*255))
	var_2 = L * (1+S) if (L < 0.5) else (L+S) - (S*L)
	var_1 = 2*L - var_2

	def hue2rgb(v1, v2, vH):
		if (vH < 0): vH += 1
		if (vH > 1): vH -= 1
		if ((6*vH)<1): return v1 + (v2-v1)*6*vH
		if ((2*vH)<1): return v2
		if ((3*vH)<2): return v1 + (v2-v1)*(2/3.0-vH)*6
		return v1
		
	R = int(255*hue2rgb(var_1, var_2, H + (1.0/3)))
	G = int(255*hue2rgb(var_1, var_2, H))
	B = int(255*hue2rgb(var_1, var_2, H - (1.0/3)))
	return (R,G,B)

def test_anvil(block_list, data_list, section_num):
	# Show an image of the chunk from above
	pixels = ""
	block_colors = {
		0: {'h':0, 's':0, 'l':0},       # Air
		1: {'h':0, 's':0, 'l':32},      # Stone
		2: {'h':94, 's':42, 'l':32},    # Grass
		3: {'h':27, 's':51, 'l':15},    # Dirt
		4: {'h':0, 's':0, 'l':25},      # Cobblestone
		8: {'h':228, 's':50, 'l':23},   # Water
		9: {'h':228, 's':50, 'l':23},   # Water
		10: {'h':16, 's':100, 'l':48},  # Lava
		11: {'h':16, 's':100, 'l':48},  # Lava
		12: {'h':53, 's':22, 'l':58},   # Sand
		13: {'h':21, 's':18, 'l':20},   # Gravel
		17: {'h':35, 's':93, 'l':15},   # Wood
		18: {'h':114, 's':64, 'l':22},  # Leaves
		24: {'h':48, 's':31, 'l':40},   # Sandstone
		37: {'h':60, 's':100, 'l':60},  # Yellow Flower
		38: {'h':0, 's':100, 'l':50},   # Red Flower
		50: {'h':60, 's':100, 'l':50},  # Torch
		51: {'h':55, 's':100, 'l':50},  # Fire
		59: {'h':123, 's':60, 'l':50},  # Crops
		60: {'h':35, 's':93, 'l':15},   # Farmland
		78: {'h':240, 's':10, 'l':85},  # Snow
		79: {'h':240, 's':10, 'l':95},  # Ice
		81: {'h':126, 's':61, 'l':20},  # Cacti
		82: {'h':7, 's':62, 'l':23},    # Clay
		83: {'h':123, 's':70, 'l':50},  # Sugarcane
		86: {'h':24, 's':100, 'l':45},  # Pumpkin
		91: {'h':24, 's':100, 'l':45},  # Jack-o-lantern
	}
	block_list = BlockArray(blocksBytes=block_list)
	for z in range(16):
		for x in range(16):
			for y in range(16*section_num, -1, -1):
				# Find the highest block in this column
				ground_height = 16*section_num
				tints = []
				block_id = block_list.blocksList[(y + z*(16*section_num) + x*(16*section_num)*16)-1]
				block_data =  0
				if (block_id == 8 or block_id == 9):
					tints.append({'h':228, 's':50, 'l':23}) # Water
				elif (block_id == 18):
					if (block_data == 1):
						tints.append({'h':114, 's':64, 'l':22}) # Redwood Leaves
					elif (block_data == 2):
						tints.append({'h':93, 's':39, 'l':10}) # Birch Leaves
					else:
						tints.append({'h':114, 's':64, 'l':22}) # Normal Leaves
				elif (block_id == 79):
					tints.append({'h':240, 's':5, 'l':95}) # Ice
				elif (block_id == 51):
					tints.append({'h':55, 's':100, 'l':50}) # Fire
				elif (block_id != 0):
					# Here is ground level
					ground_height = y
					break

			color = block_colors[block_id] if (block_id in block_colors) else {'h':0, 's':0, 'l':100}
			height_shift = (ground_height-64)*0.25
			
			final_color = {'h':color['h'], 's':color['s'], 'l':color['l']+height_shift}
			if final_color['l'] > 100: final_color['l'] = 100
			if final_color['l'] < 0: final_color['l'] = 0
			
			# Apply tints from translucent blocks
			for tint in reversed(tints):
				final_color = hsl_slide(final_color, tint, 0.4)

			rgb = hsl2rgb(final_color['h'], final_color['s'], final_color['l'])

			pixels += pack("BBB", rgb[0], rgb[1], rgb[2])
	im = Image.fromstring('RGB', (16,16), pixels)
	return im
        

def main(world_folder):
        try:
                raise TypeError
                world = McRegionWorldFolder(world_folder)  # map still only supports McRegion maps
                bb = world.get_boundingbox()
                map = Image.new('RGB', (16*bb.lenx(),16*bb.lenz()))
                t = world.chunk_count()
                try:
                        i =0.0
                        for chunk in world.iter_chunks():
                                if i % 50 ==0:
                                        sys.stdout.write("Rendering image")
                                elif i % 2 == 0:
                                        sys.stdout.write(".")
                                        sys.stdout.flush()
                                elif i % 50 == 49:
                                        sys.stdout.write("%5.1f%%\n" % (100*i/t))
                                i +=1
                                chunkmap = get_map(chunk)
                                x,z = chunk.get_coords()
                                map.paste(chunkmap, (16*(x-bb.minx),16*(z-bb.minz)))
                        print(" done\n")
                        filename = os.path.basename(world_folder)+".png"
                        map.save(filename,"PNG")
                        print("Saved map as %s" % filename)
                except KeyboardInterrupt:
                        print(" aborted\n")
                        filename = os.path.basename(world_folder)+".partial.png"
                        map.save(filename,"PNG")
                        print("Saved map as %s" % filename)
                        return 75 # EX_TEMPFAIL
                map.show()
                return 0 # NOERR
        except TypeError as e:
                print "Starting Anvil render..."
                world = AnvilWorldFolder(world_folder)
                bb = world.get_boundingbox()
                map = Image.new('RGB', (16*bb.lenx(),16*bb.lenz()))
                try:
                        
                        for chunk in world.iter_nbt():
                                ids = bytearray()
                                data = bytearray()
                                # build up the chunk in 16x16x256 max
                                for temp in chunk['Level']['Sections']:
                                        ids += (temp['Blocks'].value)
                                        data += (temp['Data'].value)
                                # up to 16 sections/levels, need how many levels
                                chunkmap = test_anvil(ids, data, len(chunk['Level']['Sections'])) 
                                x,z = chunk['Level']['xPos'], chunk['Level']['zPos']
                                map.paste(chunkmap, (16*(x.value-bb.minx),16*(z.value-bb.minz)))
                except KeyboardInterrupt:
                        map.save("anvil.partial.png")
                map.save("anvil.png")

                                
if __name__ == '__main__':
	if (len(sys.argv) == 1):
		print("No world folder specified!")
		sys.exit(64) # EX_USAGE
	world_folder = sys.argv[1]
	if (not os.path.exists(world_folder)):
		print("No such folder as "+world_folder)
		sys.exit(72) # EX_IOERR
	
	sys.exit(main(world_folder))
