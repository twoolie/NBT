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

Bug Fixes since 1.3.0
~~~~~~~~~~~~~~~~~~~~~
* generate_heightmap now ignored non-solid blocks (such as tall grass)

Backward Incompatible Changes since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* WorldFolder is no longer a class, but a factory function

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


NBT 1.2.0 (7 March 2011)
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


NBT 1.1.0 (23 September 2010)
-----------------------------

New Features since 1.0.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Region file support
* Chunk convenience class
* Example scripts for block analysis and level metadata generation

Bug Fixes since 1.0.0
~~~~~~~~~~~~~~~~~~~~~
* Allow reading and writing on the same NBTFile object
* Tests for NBT class
* Same init function for TAG_Byte_Array as other classes

Backward Incompatible Changes since 1.0.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Change order of `TAG_Byte_Array.__init__()` parameters


NBT 1.0.0 (28 February 2010)
----------------------------

* First major release
* Reads and Parses NBT files
* Generates and Writes NBT files
* Reads and writes GZipped NBT files or uncompressed File objects
