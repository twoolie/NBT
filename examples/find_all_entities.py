#!/usr/bin/env python
"""
List all entities in all chunks.

This includes entities hidden in chests, even recursively. e.g.:
minecraft:written_book in green_shulker_box in chest_minecart at -304,70,292
"""
from __future__ import print_function
import os
import sys


# local module
try:
    import nbt  # noqa: F401. Suppress flake8 warning.
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    _extrapath = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir))
    if not os.path.exists(os.path.join(_extrapath, 'nbt')):
        raise
    sys.path.append(_extrapath)
from nbt.world import WorldFolder


class Entity(object):
    def __init__(self, type, tag, parent=None):
        self.type = type
        self.tag = tag
        self.parent = parent

    def name(self):
        if self.type.startswith('minecraft:'):
            return self.type[10:]
        else:
            return self.type

    def pos(self):
        if self.parent:
            return self.parent.pos()
        elif 'Pos' in self.tag:
            return [round(xyz.value) for xyz in self.tag['Pos']]
        else:
            return [self.tag[xyz].value for xyz in 'xyz']

    def location(self, with_self=False):
        if self.type == 'minecraft:item':
            selfloc = " on ground"
        elif with_self:
            selfloc = " in " + self.name()
        else:
            selfloc = ""
        if self.parent:
            loc = selfloc + " " + self.parent.location(with_self=True)
        else:
            loc = selfloc + " at {pos[0]:d},{pos[1]:d},{pos[2]:d}". \
                    format(pos=self.pos())
        return loc[1:]

    def str(self):
        return "{0} {1}".format(self.name(), self.location())

    def repr(self):
        return "<{0} {1} {2} {3}>".format(
                    type(self).__name__,
                    id(self),
                    self.name(),
                    self.location()
                )


def yield_item_and_contents(container, parent=None):
    """yield the given item, as well as any items contained within."""
    self = Entity(container['id'].value, container, parent)
    if self.type == 'minecraft:item':
        container = container['Item']
        self = Entity(container['id'].value, container, self)
    yield self
    try:
        for item in container['Items']:
            for subitem in yield_item_and_contents(item, parent=self):
                yield subitem
    except KeyError:
        pass
    try:
        for item in container['tag']['BlockEntityTag']['Items']:
            for subitem in yield_item_and_contents(item, parent=self):
                yield subitem
    except KeyError:
        pass


def main(world_folder):
    world = WorldFolder(world_folder)

    try:
        for chunk in world.iter_nbt():
            for entity in chunk["Level"]['Entities']:
                for subentity in yield_item_and_contents(entity):
                    print(subentity.type, subentity.location())
            for entity in chunk["Level"]['TileEntities']:
                for subentity in yield_item_and_contents(entity):
                    print(subentity.type, subentity.location())

    except KeyboardInterrupt:
        return 75  # EX_TEMPFAIL

    return 0  # NOERR


if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print("No world folder specified!")
        sys.exit(64)  # EX_USAGE
    world_folder = sys.argv[1]
    # clean path name, eliminate trailing slashes:
    world_folder = os.path.normpath(world_folder)
    if (not os.path.exists(world_folder)):
        print("No such folder as "+world_folder)
        sys.exit(72)  # EX_IOERR

    sys.exit(main(world_folder))
