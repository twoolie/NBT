#!/usr/bin/env python
"""
Finds the contents of the different blocks in a level, taking different data values (sub block types) into account.
"""

import locale, os, sys

# local module
try:
    import nbt
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
from nbt.world import WorldFolder


block_counts = {}


def stats_per_chunk(chunk):
    """Given a chunk, increment the block types with the number of blocks found"""

    for block_id in chunk.iter_block():
        try:
            block_counts[block_id] += 1
        except KeyError:
            block_counts[block_id] = 1


def bounded_stats_per_chunk(chunk, block_counts, start, stop):
    """Given a chunk, return the number of blocks types within the specified selection"""
    chunk_z, chunk_x = chunk.get_coords()
    for z in range(16):
        world_z = z + chunk_z*16
        if ( (start != None and world_z < int(start[2])) or (stop != None and  world_z > int(stop[2])) ):
            # Outside the bounding box; skip to next iteration
            #print("Z break: %d,%d,%d" % (world_z,start[2],stop[2]))
            break
        for x in range(16):
            world_x = x + chunk_x*16
            if ( (start != None and world_x < int(start[0])) or (stop != None and world_x > int(stop[0])) ):
                # Outside the bounding box; skip to next iteration
                #print("X break: %d,%d,%d" % (world_x,start[0],stop[0]))
                break
            for y in range(chunk.get_max_height() + 1):
                if ( (start != None and y < int(start[1])) or (stop != None and y > int(stop[1])) ):
                    # Outside the bounding box; skip to next iteration
                    #print("Y break: %d,%d,%d" % (y,start[1],stop[1]))
                    break
                
                #print("Chunk: %d,%d Coord: %d,%d,%d" % (c['x'], c['z'],x,y,z))
                block_id = chunk.get_block(x,y,z)
                if block_id != None:
                    try:
                        block_counts[block_id] += 1
                    except KeyError:
                        block_counts[block_id] = 1


def process_region_file(region, start, stop):
    """Given a region, return the number of blocks of each ID in that region"""
    rx = region.loc.x
    rz = region.loc.z

    # Does the region overlap the bounding box at all?
    if (start != None):
        if ( (rx+1)*512-1 < int(start[0]) or (rz+1)*512-1 < int(start[2]) ):
            return
    elif (stop != None):
        if ( rx*512-1 > int(stop[0]) or rz*512-1 > int(stop[2]) ):
            return

    # Get all chunks
    print("Parsing region %s..." % os.path.basename(region.filename))
    for c in region.iter_chunks_class():
        cx, cz = c.get_coords();
        # Does the chunk overlap the bounding box at all?
        if (start != None):
            if ( (cx+1)*16 + rx*512 - 1 < int(start[0]) or (cz+1)*16 + rz*512 - 1 < int(start[2]) ):
                continue
        elif (stop != None):
            if ( cx*16 + rx*512 - 1 > int(stop[0]) or cz*16 + rz*512 - 1 > int(stop[2]) ):
                continue

        #print("Parsing chunk (" + str(cx) + ", " + str(cz) + ")...")

        # Fast code if no start or stop coordinates are specified
        # TODO: also use this code if start/stop is specified, but the complete chunk is included
        if (start == None and stop == None):
            stats_per_chunk(c)
        else:
            # Slow code that iterates through each coordinate
            bounded_stats_per_chunk(c, start, stop)


def print_results():
    locale.setlocale(locale.LC_ALL, '')
    
    # Analyze blocks
    
    block_total = 0
    
    for block_id,block_count in block_counts.items():
        print(locale.format_string("%20s: %12d", (block_id, block_count)))
        block_total += block_count
    
    solid_blocks = block_total - block_counts ['air']
    solid_ratio = (solid_blocks+0.0)/block_total
    print(locale.format_string("%d total blocks in world, %d are non-air (%0.4f", (block_total, solid_blocks, 100.0*solid_ratio))+"%)")


def main(world_folder, start=None, stop=None):
    world = WorldFolder(world_folder)

    try:
        for region in world.iter_regions():
            process_region_file(region, start, stop)

    except KeyboardInterrupt:
        print('Keyboard interrupt!')
        print_results(block_counts)
        return 75 # EX_TEMPFAIL

    print_results()
    return 0 # EX_OK


if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print("No world folder specified! Usage: %s <world folder> [minx,miny,minz maxx,maxy,maxz]" % sys.argv[0])
        sys.exit(64) # EX_USAGE
    world_folder = sys.argv[1]
    # clean path name, eliminate trailing slashes. required for os.path.basename()
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        print("No such folder as "+world_folder)
        sys.exit(72) # EX_IOERR
    start,stop = None,None
    if (len(sys.argv) == 4):
        # A min/max corner was specified
        start_str = sys.argv[2][1:-1] # Strip parenthesis...
        start = tuple(start_str.split(',')) # and convert to tuple
        stop_str = sys.argv[3][1:-1] # Strip parenthesis...
        stop = tuple(stop_str.split(',')) # and convert to tuple
    
    sys.exit(main(world_folder, start, stop))
