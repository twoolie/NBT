#!/usr/bin/env python

# Create a file that can be used as a basic level.dat file with all required fields
# http://www.minecraftwiki.net/wiki/Alpha_Level_Format#level.dat_Format

import time
import random

# local module
try:
    # Yes, yes, I know. Importing * may give namespace collisions. Fix it if you like.
    from nbt import *
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(sys.path[0],os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
    from nbt import *


level = NBTFile() # Blank NBT
level.name = "Data"
level.tags.extend([
	TAG_Long(name="Time", value=1),
	TAG_Long(name="LastPlayed", value=int(time.time())),
	TAG_Int(name="SpawnX", value=0),
	TAG_Int(name="SpawnY", value=2),
	TAG_Int(name="SpawnZ", value=0),
	TAG_Long(name="SizeOnDisk", value=0),
	TAG_Long(name="RandomSeed", value=random.randrange(1,9999999999)),
	TAG_Int(name="version", value=19132),
	TAG_String(name="LevelName", value="Testing")
])

player = TAG_Compound()
player.name = "Player"
player.tags.extend([
	TAG_Int(name="Score", value=0),
	TAG_Int(name="Dimension", value=0)
])
inventory = TAG_Compound()
inventory.name = "Inventory"
player.tags.append(inventory)
level.tags.append(player)

print level.pretty_tree()
#level.write_file("level.dat")