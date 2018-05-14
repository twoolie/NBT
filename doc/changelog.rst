Changelog
=========

NBT currently only uses major and minor releases. Patch versions exist as
commits in the master trunk, but are not enumerated.


NBT Trunk
---------
Git trunk can be found at https://github.com/twoolie/NBT/tree/master

Bug Fixes since 1.5.0
~~~~~~~~~~~~~~~~~~~~~
* None


Known Bugs
~~~~~~~~~~
See https://github.com/twoolie/NBT/issues

* It is posible to access the NBT structure of any world folder, including
  McRegion and Anvil worlds. However, chunk specifics (such as the location
  of blocks in the NBT structure) are only available for McRegion, not for
  Anvil.
* The name of a variable generally only supports 2-byte Unicode characters (the
  Basic Multilingual Plane). For Full Unicode support, use Python 3.3 or higher,
  or compile Python --with-wide-unicode.


NBT 1.5.0 (14 May 2018)
---------------------------

New Features since 1.4.1
~~~~~~~~~~~~~~~~~~~~~~~~
* Support for Long Arrays (used in Minecraft 1.13 and higher) (#95)

Bug Fixes since 1.4.1
~~~~~~~~~~~~~~~~~~~~~~~~
* Faster reading chunks with corrupt header. (#76)

Changes in Auxiliary Scripts since 1.4.1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Add examples/player_print.py script (courtesy k1988).
* Automatic testing now also runs Python 3.4, 3.5, 3.6 and pypy3.
* Review and minor improvements of tests.
* PEP8-compatibility improvements of the code (courtesy suresttexas00)


NBT 1.4.1 (27 October 2013)
---------------------------

New Features since 1.4.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Change indentation from tabs to spaces.


NBT 1.4.0 (27 October 2013)
---------------------------

New Features since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Added documentation.
* WorldFolder.iter_chunks() returns Chunk subclass (McRegionChunk / AnvilChunk)
* Add exception when opening files too small to be a region file.
* Examples/map.py example now works with Python 3 as well.
  The recommended library is Pillow, a fork of PIL that supports Python 3.
* Rewrote chunk writing algorithm in nbt.region, and added lots of code checks
  to verify that it never overwrite chunks.
* Support writing to corrupt region files, working around corrupt parts.
* Support reading uncompressed chunks in region files.
* Added detection for overlapping chunks in region files.
* Added RegionFileFormatError exception.
* Allow easy iteration over chunks in a RegionFile:
  `for chunk in RegionFile(filename)`
* RegionFile.iter_chunks() now silently ignores unreadable chunks.
* Better display of filenames in NBTFile and RegionFiles when initialised with
  a fileobject.
* Truncate region file size when possible.
* Add RegionFile.get_chunk_metadata() method.
* Expose more detailed read and write methods in RegionFile: get_blockdata(), 
  get_nbt(), get_chunk(), write_blockdata(), write_chunk().

Bug Fixes since 1.3.0
~~~~~~~~~~~~~~~~~~~~~
* generate_heightmap now ignores non-solid blocks (such as tall grass).
* Fix behavior of `__delitem__` in TAG_list and TAG_Compound.
* Fix infinite loop while writing a chunk changing the way in which free 
  space is searched in the region file.
* Fixed a bug that sometimes made write chunks in the region file header.
* Fixed a bug that corrupted the file when writing a chunk that was between
  4093 and 4096 bytes after compression.
* Now possible to write and immediately read chunks in region files.
* Allow increase in region file size.
* Allow trailing slash in world folder in example scripts
* Replace all `import *` with specific imports.
* Support for (empty) TAG_Lists with TAG_End objects.

Changes in Auxiliary Scripts since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Automatic testing now also runs example scripts
* Automatic testing now also runs Python 3.3
* Code for automatic documentation generation forked in a seperate package,
  sphinxcontrib-restbuilder.
* Automatic testing for Python 2.6 now requires unittest2 package.
* Documented automatic code generation and simplified Makefile.

Backward Incompatible Changes since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* WorldFolder is no longer a class, but a factory function that returns
  (a subclass of) a _BaseWorldFolder instance.
* The fileobj parameter in `RegionFile(fileobj)` is no longer closed
  (similar to the behaviour of e.g. GZipFile). It is the callers
  responsibility to close these files.
* RegionFile.get_chunk() raises InconceivedChunk when a chunk does not exist
  instead of returning None.
* Exceptions raised while reading chunks are always a RegionFileFormatError or
  subclass thereof. GZip, zlib and nbt.MalformedFileError are no longer raised.
* init_header(), parse_header() and parse_chunk_headers() in RegionFile are no
  longer public methods.

Deprecated features since 1.3.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Constants in nbt.region moved to module level. They are still available in
  the class for backwards compatibility.
* `nbt.region.RegionFile.header` and `nbt.region.RegionFile.chunk_headers` are
  deprecated in favour of `nbt.region.RegionFile.metadata`. They are still
  available for backward compatibility.
* Deprecate `RegionFile.get_chunks()` and `RegionFile.get_chunk_coords()` in
  favour of `RegionFile.get_metadata()`.
* RegionFile.get_chunk() method may later be changed to return a Chunk() object.
  Use RegionFile.get_nbt() to retain the current behaviour.


NBT 1.3.0 (19 March 2012)
-------------------------

New Features since 1.2.0
~~~~~~~~~~~~~~~~~~~~~~~~
* Python 3 support
* NBT_Tag objects behave like native Python objects

  - TAG_Byte_Array, TAG_Int_Array and TAG_List are now a MutableSequence
  - TAG_Compound is now a MutableMapping
  - TAG_String is now a Sequence

* Improved printing of TAGs (`__str__` and `__repr__`) for easier debugging
* Added examples script for listing mobs, listing chest content, display
  world seed, and counting Biome data
* Block analysis example takes data value of blocks into account
* Subclass of Worldfolder: McRegionWorldfolder and AnvilWorldFolder
* Added iterator functions: iter_chunks, iter_nbt, iter_regions in
  WorlFolder and iter_nbt in RegionFile
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
