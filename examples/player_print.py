#!/usr/bin/env python
"""
Finds and prints different entities in a game file, including mobs, items, and vehicles.
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
    import nbt

def player(uuid, path):
    nbtfile = nbt.nbt.NBTFile(path,'rb')
    if not "bukkit" in nbtfile:
        return
    if not "lastPlayed" in nbtfile["bukkit"]:
        return
    print("%s,%s,%s" % ( nbtfile["bukkit"]["lastKnownName"], uuid, nbtfile["bukkit"]["lastPlayed"]))


def main(world_folder):
    for root, dirs, files in os.walk(world_folder):
        for file in files:
            if file.endswith(".dat") and len(file) == 40:
                uuid = file[0:36]
                player(uuid, os.path.join(root, file))

if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print("No playerdata folder specified!")
        sys.exit(64) # EX_USAGE
    world_folder = sys.argv[1]
    # clean path name, eliminate trailing slashes:
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        print("No such folder as "+world_folder)
        sys.exit(72) # EX_IOERR
    
    sys.exit(main(world_folder))
