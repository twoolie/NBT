#!/usr/bin/env python
"""
Print the block names and counts for a layer in an Anvil chunk
Updated to support Anvil format version 1631
Section specific code moved to AnvilChunk class
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


def main(world_folder, chunkx, chunkz, height):

    world = nbt.world.WorldFolder(world_folder)
    if not isinstance(world, nbt.world.AnvilWorldFolder):
        print("%s is not an Anvil world" % (world_folder))
        return 65 # EX_DATAERR

    blocks = {}

    try:
        chunk = world.get_chunk(chunkx, chunkz)
        for z in range(0, 16):
            for x in range(0, 16):
                b = chunk.get_block(x, height, z)
                if b != None:
                    if b not in blocks:
                        blocks[b] = 0
                    blocks[b] = blocks[b] + 1

        print("Chunk (%i,%i) Height %i" % (chunkx, chunkz, height))
        for n in blocks.keys():
            print("%s: %i" % (n, blocks[n]))

    except nbt.region.InconceivedChunk:
        print("Inconceived chunk")

    return 0 # NOERR


def usage(message=None, appname=None):
    if appname == None:
        appname = os.path.basename(sys.argv[0])
    print("Usage: %s WORLD_FOLDER CHUNK-X CHUNK-Z BLOCKHEIGHT-Y" % appname)
    if message:
        print("%s: error: %s" % (appname, message))


if __name__ == '__main__':
    if (len(sys.argv) != 5):
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
        height = int(sys.argv[4])
    except ValueError:
        usage('Block height Y-coordinate should be an integer')
        sys.exit(64) # EX_USAGE

    # clean path name, eliminate trailing slashes:
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        usage("No such folder as "+world_folder)
        sys.exit(72) # EX_IOERR

    sys.exit(main(world_folder, chunkx, chunkz, height))
