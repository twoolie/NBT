Changelog
=========

NBT currently only uses major and minor releases. Patch versions exist as
commits in the master trunk, but are not enumerated.


NBT Trunk
---------
Git trunk can be found at https://github.com/twoolie/NBT/tree/master

New Features since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Added documentation
* Automatic testing now also runs example scripts
* WorldFolder.iter_chunks() returns Chunk subclass (McRegionChunk / AnvilChunk)
* Add exception when opening files too small to be a region file.

Bug Fixes since 1.3.0
~~~~~~~~~~~~~~~~~~~~~
* generate_heightmap now ignored non-solid blocks (such as tall grass)
* Fix `__delitem__` in TAG_list.
* Fix behavior of `__delitem__` on TAG_Compound
* Fix infinite loop while writing a chunk changing the way in which free space is searched in the region file

Backward Incompatible Changes since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* WorldFolder is no longer a class, but a factory function
* The fileobj parameter in `RegionFile(fileobj)` is no longer closed
  (similar to the behaviour of e.g. GZipFile). It is the callers
  responsibility to close these files.

Known Bugs
~~~~~~~~~~
See https://github.com/twoolie/NBT/issues


NBT 1.3.0 (19 March 2012)
-------------------------

New Features since 1.2.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Python 3 support
* NBT_Tag objects behave like native Python objects
  - TAG_Byte_Array, TAG_Int_Array and TAG_List are now a MutableSequence
  - TAG_Compound is now a MutableSequence
  - TAG_String is now a Sequence
* Improved printing of TAGs (`__str__` and `__repr__`) for easier debugging
* Added examples script for listing mobs, listing chest content, display
  world seed, and counting Biome data
* Block analysis example takes data value of blocks into account
* Subclass of Worldfolder: McRegionWorldfolder and AnvilWorldFolder
* Added iterator functions: iter_chunks, iter_nbt, iter_regions in
  WorlFolder and iter_nbt in 
* Move unit tests and sample file to tests directory

Bug Fixes since 1.2.0
~~~~~~~~~~~~~~~~~~~~~
* Travis (automatic testing) support
* Test file is no longer overwritten.
* Consistent Unix line-endings and tabs for indentation
* raise InconceivedChunk if a requested chunk was not yet generated
* Can instantiate a RegionFile without associating it with an existing file
* Use sysexit error codes instead of syserror codes in example scripts

Backward Incompatible Changes since 1.2.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Dropped support for Python 2.4 and 2.5
* Use native Python bytearray() to store TAG_Byte_Array().value, instead of
  string, list or array.array
* NBT now expects Unicode instances for strings (e.g. for name in TAGs and
  keys in TAG_Compound), while it expects bytes (or BytesIO) for byte
  arrays and buffers.
* Instantiating a WorldFolder now returns either a McRegionWorldfolder or
  AnvilWorldFolder


NBT 1.2.0 (7 March 2012)
------------------------

New Features since 1.1.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Support for TAG_Int_Array (required for Minecraft Anvil worlds)
* 15x Speed improvement of `BlockArray.__init__` in nbt.chunk
* Initial support for world folders: world.py
* Examples can be executed in-place, without installing NBT
* Map example prints entire world (only works for McRegion worlds)

Bug Fixes since 1.1.0
~~~~~~~~~~~~~~~~~~~~~
* Support for data bits (this was previously broken)
* Region file checks for inconsistent chunk lengths (this may detect
  truncated region files)
* TAG_List behave like a Python list (is iterable and has a length)

Backward Incompatible Changes since 1.1.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Method `RegionFile.get_chunks()` is deprecated in favour of
  `RegionFile.get_chunk_coords()`


NBT 1.1.0 (23 September 2011)
-----------------------------

New Features since 1.0.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Region file support
* Chunk convenience class
* Example scripts for block analysis and level metadata generation

Bug Fixes since 1.0.0
~~~~~~~~~~~~~~~~~~~~~
* Allow reading and writing on the same NBTFile object
* Same init function for TAG_Byte_Array as other classes
* Unit tests for NBT class

Backward Incompatible Changes since 1.0.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Change order of `TAG_Byte_Array.__init__()` parameters


NBT 1.0.0 (28 February 2011)
----------------------------

* First stable release
* Reads and Parses NBT files
* Generates and Writes NBT files
* Reads and writes GZipped NBT files or uncompressed File objects


NBT 0.9.0 (15 December 2010)
----------------------------
See https://github.com/twoolie/NBT/tree/fe3467fec6d18a6445bc850e9386e1be9e4e1299


NBT 0.8.0 (27 November 2010)
----------------------------
See https://github.com/twoolie/NBT/tree/67e5f0acdad838e4652d68e7342c362d786411a0


NBT 0.7.0 (2 November 2010)
----------------------------
See https://github.com/twoolie/NBT/tree/8302ab1040fca8aabd4cf0ab1f40105889c24464


NBT 0.6.0 (29 October 2010)
----------------------------
See https://github.com/twoolie/NBT/tree/0f0cae968f1fc2d5e5f2cabb37f79bb7910ca7e3


NBT 0.5.0 (8 August 2010)
----------------------------
See https://github.com/twoolie/NBT/tree/7d289f0cc4cf91197108569ba361cff934ebaf38

* First public release
* Pre-release (not stable yet)
