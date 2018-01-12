#!/usr/bin/env python
"""
Counter the number of biomes in the world. Works only for Anvil-based world folders.
"""
import locale, os, sys
from struct import pack, unpack

# local module
try:
    import nbt
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
from nbt.region import RegionFile
from nbt.chunk import Chunk
from nbt.world import AnvilWorldFolder,UnknownWorldFormat

BIOMES = {
    0 : "Ocean",
    1 : "Plains",
    2 : "Desert",
    3 : "Mountains",
    4 : "Forest",
    5 : "Taiga",
    6 : "Swamp",
    7 : "River",
    8 : "Nether",
    9 : "Sky",
    10: "Frozen Ocean",
    11: "Frozen River",
    12: "Ice Plains",
    13: "Ice Mountains",
    14: "Mushroom Island",
    15: "Mushroom Shore",
    16: "Beach",
    17: "Desert Hills",
    18: "Forest Hills",
    19: "Taiga Hills",
    20: "Mountains Edge",
    21: "Jungle",
    22: "Jungle Hills",
    23: "Jungle Edge",
    24: "Deep Ocean",
    25: "Stone Beach",
    26: "Cold Beach",
    27: "Birch Forest",
    28: "Birch Forest Hills",
    29: "Roofed Forest",
    30: "Cold Taiga",
    31: "Cold Taiga Hills",
    32: "Mega Taiga",
    33: "Mega Taiga Hills",
    34: "Extreme Hills",
    35: "Savanna",
    36: "Savanna Plateau",
    37: "Mesa",
    38: "Mesa Plateau F",
    39: "Mesa Plateau",
    127: "The Void",
    129: "Sunflower Plains",
    130: "Desert M",
    131: "Extreme Hills M",
    132: "Flower Forest",
    133: "Taiga M",
    134: "Swampland M",
    140: "Ice Plains Spikes",
    149: "Jungle M",
    151: "Jungle Edge M",
    155: "Birch Forest M",
    156: "Birch Forest Hills M",
    157: "Roofed Forest M",
    158: "Cold Taiga M",
    160: "Mega Spruce Taiga",
    161: "Redwood Taiga Hills M",
    162: "Extreme Hills+ M",
    163: "Savanna M",
    164: "Savanna Plateau M",
    165: "Mesa(Bryce)",
    166: "Mesa Plateau F M",
    167: "Mesa Plateau M"
    # 255: "Not yet calculated",
}


def print_results(biome_totals):
    locale.setlocale(locale.LC_ALL, '')
    for id,count in enumerate(biome_totals):
        # Biome ID 255 is ignored. It means it is not calculated by Minecraft yet
        if id == 255 or (count == 0 and id not in BIOMES):
            continue
        if id in BIOMES:
            biome = BIOMES[id]+" (%d)" % id
        else:
            biome = "Unknown (%d)" % id
        print(locale.format_string("%-25s %10d", (biome,count)))


def main(world_folder):
    world = AnvilWorldFolder(world_folder)  # Not supported for McRegion
    if not world.nonempty():  # likely still a McRegion file
        sys.stderr.write("World folder %r is empty or not an Anvil formatted world\n" % world_folder)
        return 65  # EX_DATAERR
    biome_totals = [0]*256 # 256 counters for 256 biome IDs
    
    try:
        for chunk in world.iter_nbt():
            for biomeid in chunk["Level"]["Biomes"]:
                biome_totals[biomeid] += 1

    except KeyboardInterrupt:
        print_results(biome_totals)
        return 75 # EX_TEMPFAIL
    
    print_results(biome_totals)
    return 0 # NOERR


if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print("No world folder specified!")
        sys.exit(64) # EX_USAGE
    world_folder = sys.argv[1]
    # clean path name, eliminate trailing slashes:
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        print("No such folder as "+world_folder)
        sys.exit(72) # EX_IOERR
    
    sys.exit(main(world_folder))
