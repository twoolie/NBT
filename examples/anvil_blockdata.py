#!/usr/bin/env python
"""
Print the block ID and data for a layer in a Anvil chunk
This supports regular blocks with ID 0-255 and non-standard blocks with ID 256-4095.
"""
import os, sys
import itertools

try:
    zip_longest = itertools.zip_longest
except AttributeError:
    zip_longest = itertools.izip_longest

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


def array_4bit_to_byte(array):
    """Convert a 2048-byte array of 4096 4-bit values to an array of 4096 1-byte values.
    The result is of type bytearray().
    Note that the first byte of the created arrays contains the LEAST significant 
    bits of the first byte of the Data. NOT to the MOST significant bits, as you 
    might expected. This is because Minecraft stores data in that way.
    """
    def iterarray(array):
        for b in array:
            yield(b & 15) # Little end of the byte
            yield((b >> 4) & 15) # Big end of the byte
    return bytearray(iterarray(array))

def array_byte_to_4bit(array):
    """Convert an array of 4096 1-byte values to a 2048-byte array of 4096 4-bit values.
    The result is of type bytearray().
    Any values larger than 16 are taken modulo 16.
    Note that the first byte of the original array will be placed in the LEAST 
    significant bits of the first byte of the result. Thus NOT to the MOST 
    significant bits, as you might expected. This is because Minecraft stores 
    data in that way.
    """
    def iterarray(array):
        arrayiter = iter(array)
        for b1 in arrayiter:
            b2 = next(arrayiter, 0)
            yield(((b2 & 15) << 4) + (b1 & 15))
    return bytearray(iterarray(array))

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    # Taken from itertools recipe.
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def print_chunklayer(blocks, data, add, yoffset):
    blocks = list(blocks[yoffset*256:(yoffset+1)*256])
    data = array_4bit_to_byte(data[yoffset*128:(yoffset+1)*128])
    if add is not None:
        add = array_4bit_to_byte(add[yoffset*128:(yoffset+1)*128])
        for i,v in enumerate(add):
            blocks[i] += 256*v
    
    assert len(blocks) == 256
    assert len(data) == 256
    
    for row in grouper(zip(blocks,data), 16):
        print (" ".join(("%4d:%-2d" % block) for block in row))

def get_section(world, chunkx, chunky, chunkz):
    """Given a world folder, return the requested section.
    If it is not defined, raise InconceivedChunk."""
    chunk = world.get_nbt(chunkx, chunkz) # may raise InconceivedChunk
    for section in chunk['Level']['Sections']:
        if section['Y'].value == chunky:
            return section
    raise nbt.region.InconceivedChunk("Section not defined")

def main(world_folder, chunkx, chunkz, height):
    world = nbt.world.WorldFolder(world_folder)
    if not isinstance(world, nbt.world.AnvilWorldFolder):
        print("%s is not an Anvil world" % (world_folder))
        return 65 # EX_DATAERR
    chunky, yoffset = divmod(height, 16)
    try:
        section = get_section(world, chunkx, chunky, chunkz)
        try:
            blocks = section['Blocks'].value
            data = section['Data'].value
        except (KeyError, AttributeError):
            blocks = bytearray(4096)
            data = bytearray(2048)
        try:
            add = section['Add'].value
        except (KeyError, AttributeError):
            add = None
    except nbt.region.InconceivedChunk:
        print("Section undefined")
        blocks = bytearray(4096)
        data = bytearray(2048)
        add = None
    
    print_chunklayer(blocks, data, add, yoffset)
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
