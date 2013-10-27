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
from nbt.world import WorldFolder

class Position(object):
    def __init__(self, x,y,z):
        self.x = x
        self.y = y
        self.z = z

class Entity(object):
    def __init__(self, type, pos):
        self.type  = type
        self.pos   = Position(*pos)


def entities_per_chunk(chunk):
    """Given a chunk, find all entities (mobs, items, vehicles)"""
    entities = []
    for entity in chunk['Entities']:
        x,y,z = entity["Pos"]
        entities.append(Entity(entity["id"].value, (x.value,y.value,z.value)))
    return entities


def print_results(entities):
    locale.setlocale(locale.LC_ALL, '')
    for entity in entities:
        print("%s at %s,%s,%s" % \
            (entity.type,\
            locale.format("%0.1f",entity.pos.x,grouping=True),\
            locale.format("%0.1f",entity.pos.y,grouping=True),\
            locale.format("%0.1f",entity.pos.z,grouping=True)))


def main(world_folder):
    world = WorldFolder(world_folder)
    
    try:
        for chunk in world.iter_nbt():
            print_results(entities_per_chunk(chunk["Level"]))

    except KeyboardInterrupt:
        return 75 # EX_TEMPFAIL
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
