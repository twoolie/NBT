#!/usr/bin/env python
"""
Find all books in all chunks and output the contents
"""
import os
import sys
import json
import hashlib

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
    TYPE_TRANSLATE = {
        386: 'minecraft:writable_book',
        387: 'written_book',
    }

    def __init__(self, type, tag, parent=None):
        try:
            type = self.TYPE_TRANSLATE[type]
        except KeyError:
            pass
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


class Book(object):
    def __init__(self):
        self.locations = []
        self.title = ''
        self.author = ''
        self.pages = []
        self.hash = ''

    @classmethod
    def from_entity(cls, entity):
        self = cls()
        print(entity.type, entity.location())
        try:
            book = entity.tag['tag']
        except KeyError:
            return self
        try:
            generation = int(book['generation'].value)
        except KeyError:
            generation = 0
        self.locations = [(generation, entity.type, entity.location())]
        self.title = book['title'].value
        self.author = book['author'].value
        self.pages = []
        hash = hashlib.md5()
        hash.update(self.title.encode('utf-8'))
        hash.update(self.author.encode('utf-8'))
        for page in book['pages']:
            try:
                page_text = json.loads(page.value)
            except (KeyError, json.decoder.JSONDecodeError):
                page_text = page.value
            try:
                page_text = str(page_text['text'])
            except (KeyError, TypeError):
                page_text = str(page_text)
            self.pages.append(page_text)
            hash.update(page_text.encode('utf-8'))
        self.hash = hash.digest()
        return self

    def __str__(self):
        bookstr = []
        bookstr.append('"{0}" by {1}'.format(self.title, self.author))
        for generation, booktype, location in self.locations:
            bookstr.append('{0}{1} {2}'.format(
                generation * "copy of ", booktype, location)
            )
        for no, page in enumerate(self.pages):
            bookstr.append("---- page {0} ---------".format(no+1))
            bookstr.append(page)
        bookstr.append("-----------------------")
        return "\n".join(bookstr)


class Library(object):
    """Collection of unique books."""

    def __init__(self):
        self.collection = {}

    def add_book(self, entity):
        book = Book.from_entity(entity)
        if (not book.pages) or (not book.hash) or (not book.locations):
            print("Not a book:")
            print(entity.tag.pretty_tree())
        elif book.hash in self.collection:
            location = book.locations[0]
            self.collection[book.hash].locations.append(location)
        else:
            self.collection[book.hash] = book

    def books(self):
        return self.collection.values()


def main(world_folder):
    world = WorldFolder(world_folder)

    library = Library()
    WRITTEN_BOOKS = ('minecraft:writable_book', 'minecraft:written_book')
    try:
        # chunkno = 0
        for chunk in world.iter_nbt():
            # chunkno += 1
            # print("chunk {0}".format(chunkno))
            for entity in chunk["Level"]['Entities']:
                for subentity in yield_item_and_contents(entity):
                    if subentity.type in WRITTEN_BOOKS:
                        # sys.stdout.write('.')
                        library.add_book(subentity)
            for entity in chunk["Level"]['TileEntities']:
                for subentity in yield_item_and_contents(entity):
                    if subentity.type in WRITTEN_BOOKS:
                        # sys.stdout.write('.')
                        library.add_book(subentity)

    except KeyboardInterrupt:
        return 75  # EX_TEMPFAIL
    sys.stdout.write('\n')
    for no, book in enumerate(library.books()):
        print('==== book {0} ========='.format(no+1))
        print(book)
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
