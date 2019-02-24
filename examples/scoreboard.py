#!/usr/bin/env python

"""
Prints out raw scoreboard data.
"""

import os,sys

# local module
try:
    import nbt
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
from nbt.nbt import NBTFile, TAG_Long, TAG_Int, TAG_String, TAG_List, TAG_Compound

def main(world_folder, show=True):
    scorefile = world_folder + '/data/scoreboard.dat'
    scores = NBTFile(scorefile,'rb')

    for player in scores["data"]["PlayerScores"]:
        print("%s: %d %s" % (player["Name"], player["Score"].value, player["Objective"].value))

if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print("No world folder specified!")
        sys.exit(64) # EX_USAGE
    if sys.argv[1] == '--noshow' and len(sys.argv) > 2:
        show = False
        world_folder = sys.argv[2]
    else:
        show = True
        world_folder = sys.argv[1]
    # clean path name, eliminate trailing slashes. required for os.path.basename()
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        print("No such folder as "+world_folder)
        sys.exit(72) # EX_IOERR

    sys.exit(main(world_folder, show))