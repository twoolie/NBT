#!/usr/bin/env python
"""
Finds and prints coordinates of a required block, try with:
                  <worldpath> <x> <z> <range> <block>
./block_finder.py ./MyWorld    1   1     2    spawner
"""
import os, sys
# local module
try:
    import nbt
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
import nbt

def main(world_folder, chunkx, chunkz, chunkrange, block):
    world = nbt.world.WorldFolder(world_folder)
    if not isinstance(world, nbt.world.AnvilWorldFolder):
        print("%s is not an Anvil world" % (world_folder))
        return 65 # EX_DATAERR
    fromchunkx = chunkx - chunkrange
    fromchunkz = chunkz - chunkrange
    tochunkx = chunkx + chunkrange
    tochunkz = chunkz + chunkrange
    print("Preparing to scan chunk from %i:%i to chunk %i:%i for a %s" % (fromchunkx, fromchunkz, tochunkx, tochunkz, block))
    try:
        for chunkx in range(fromchunkx, tochunkx):
            for chunkz in range(fromchunkz, tochunkz):
                # print("Scanning chunk %i:%i" % (chunkx, chunkz))
                chunk = world.get_chunk(chunkx, chunkz)
                for z in range(0, 16):
                    for x in range(0, 16):
                        for height in range(0, 255):
                            b = chunk.get_block(x, height, z)
                            if b != None and b == block:
                                blockx = (chunkx * 16 + x)
                                blockz = (chunkz * 16 + z)
                                print("%s found at %i:%i:%i" % (b, blockx, height, blockz))
    except KeyboardInterrupt:
        print('Keyboard interrupt!')
        return 75 # EX_TEMPFAIL
    return 0

def usage(message=None, appname=None):
    if appname == None:
        appname = os.path.basename(sys.argv[0])
    print("Usage: %s WORLD_FOLDER CHUNK-X CHUNK-Z RANGE BLOCK" % appname)
    if message:
        print("%s: error: %s" % (appname, message))

if __name__ == '__main__':
    if (len(sys.argv) != 6):
        usage()
        sys.exit(64) # EX_USAGE
    world_folder = sys.argv[1]
    try:
        chunkx = int(sys.argv[2])
    except ValueError:
        usage('Chunk X-coordinate should be an integer')
        sys.exit(64) # EX_USAGE
    try:
        chunkz = int(sys.argv[3])
    except ValueError:
        usage('Chunk Z-coordinate should be an integer')
        sys.exit(64) # EX_USAGE
    try:
        chunkrange = int(sys.argv[4])
    except ValueError:
        usage('Chunk range should be an integer')
        sys.exit(64) # EX_USAGE
    try:
        block = str(sys.argv[5])
    except ValueError:
        usage('Block should be an string')
        sys.exit(64) # EX_USAGE
    # clean path name, eliminate trailing slashes:
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        usage("No such folder as "+world_folder)
        sys.exit(72) # EX_IOERR
    sys.exit(main(world_folder, chunkx, chunkz, chunkrange, block))
