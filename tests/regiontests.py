#!/usr/bin/env python
import sys,os
import tempfile, shutil
from io import BytesIO
import logging
import random
import time
import zlib

import unittest
try:
    from unittest import skip as _skip
except ImportError:
    # Python 2.6 has an older unittest API. The backported package is available from pypi.
    import unittest2 as unittest

# local modules
from utils import open_files

# Search parent directory first, to make sure we test the local nbt module, 
# not an installed nbt module.
parentdir = os.path.realpath(os.path.join(os.path.dirname(__file__),os.pardir))
if parentdir not in sys.path:
    sys.path.insert(1, parentdir) # insert ../ just after ./

from nbt.region import RegionFile, RegionFileFormatError, NoRegionHeader, \
    RegionHeaderError, ChunkHeaderError, ChunkDataError, InconceivedChunk
from nbt.nbt import NBTFile, TAG_Compound, TAG_Byte_Array, TAG_Long, TAG_Int, TAG_String

REGIONTESTFILE = os.path.join(os.path.dirname(__file__), 'regiontest.mca')

### Helper Functions and Classes ###

def generate_level(bytesize = 4):
    """Generate a level, which is a given size in bytes."""
    level = NBTFile() # Blank NBT
    def append_byte_array(name, bytesize=1000):
        bytesize -= len(name)
        bytesize -= 7
        # byte_array = TAG_Byte_Array(name=name, value=bytearray([random.randrange(256) for i in range(bytesize)]))
        # level.append(byte_array)
        byte_array = TAG_Byte_Array(name=name)
        byte_array.value = bytearray([random.randrange(256) for i in range(bytesize)])
        level.tags.append(byte_array)
    random.seed(123456789) # fixed seed to give predictable results.
    if bytesize < 13:
        raise ValueError("NBT file size is at least 13 bytes")
    # 4 bytes TAG_Compound overhead, 13 bytes TAG_Byte_Array overhead.
    bytesize -= 4 # deduce overhead bytes
    i = 1
    while bytesize > 1500:
        append_byte_array("%06d" % i, 1000)
        i += 1
        bytesize -= 1000
    append_byte_array("last", bytesize)
    return level

def generate_compressed_level(minsize = 2000, maxsize = None):
    """
    Generate a level, which -when zlib compressed- is the given size in bytes.
    Note: this returns the *UNCOMPRESSED* NBT file.
    """
    logger = logging.getLogger("nbt.tests.regiontests")
    if maxsize == None:
        maxsize = minsize
    targetsize = (minsize + maxsize) // 2
    bytesize = targetsize
    c = None
    tries = 0
    while True:
        # Generate a level, encode to binary and compress
        level = generate_level(bytesize)
        b = BytesIO()
        level.write_file(buffer=b)
        b = b.getvalue()
        assert len(b) == bytesize
        c = zlib.compress(b, 1)
        # check if the compressed size is sufficient.
        resultsize = len(c)
        logger.debug("try %d: uncompressed %d bytes -> compressed %d bytes" % \
                     (tries, bytesize, resultsize))
        if minsize <= resultsize <= maxsize:
            break
        # size is not good enough. Try again, with new targetsize.
        bytesize = int(round(bytesize * targetsize / resultsize))
        tries += 1
        if tries > 20:
            sys.stderr.write(("Failed to generate NBT file of %d bytes after %d tries. " + \
                             "Result is %d bytes.\n") % (targetsize, tries, resultsize))
            break
    return level

class PedanticFileWrapper(object):
    """Pedantic wrapper around a file object. 
    Is guaranteed to raise an IOError if an attempt is made to:
    - seek to a location larger than the file
    - read behind the file boundary
    Only works for random access files that support seek() and tell().
    """
    def __init__(self, stream):
        """Create a new wrapper. stream must be a file object."""
        self.__stream = stream
    def seek(self, offset, whence = 0):
        pos = self.__stream.tell()
        self.__stream.seek(0, 2) # end of file
        length = self.__stream.tell()
        if whence == 1:
            offset = pos + offset
        elif whence == 2:
            offset = length + offset
        result = self.__stream.seek(offset)
        if offset > length:
            raise IOError("Attempt to seek at offset %d for file of %d bytes" % (offset, length))
        elif offset < 0:
            raise IOError("Attempt to seek at offset %d for file of %d bytes" % (offset, length))
        return result
    def read(self, size = -1):
        pos = self.__stream.tell()
        self.__stream.seek(0, 2) # end of file
        length = self.__stream.tell()
        self.__stream.seek(pos)
        if pos + size > length:
            raise IOError("Attempt to read bytes %d to %d from file of %d bytes" % \
                        (pos, pos + size, length))
        return self.__stream.read(size)
    def __getattr__(self, name):
        return getattr(self.__stream, name)
    def __str__(self):
        return str(self.__stream)
    def __repr__(self):
        return str(self.__stream)


### Actual Test Classes ###

class ReadWriteTest(unittest.TestCase):
    """Test to read, write and relocate chunks in a region file."""
    
    """
    All tests operate on regiontest.mca, is a 27-sector large region file, which looks like:
    sector 000: locations
    sector 001: timestamps
    sector 002: chunk 6 ,0  part 1/1
    sector 003: chunk 7 ,0  part 1/1 <<-- minor warning: unused bytes not zeroed
    sector 004: empty                <<-- minor warning: bytes not zeroed
    sector 005: chunk 8 ,0  part 1/1
    sector 006: chunk 9 ,0  part 1/1
    sector 007: chunk 10,0  part 1/1 <<-- deprecated encoding (gzip = 1)
    sector 008: chunk 11,0  part 1/1 <<-- unknown encoding (3)
    sector 009: chunk 2 ,0  part 1/1 <<-- uncompressed (encoding 0)
    sector 010: empty
    sector 011: empty
    sector 012: chunk 3 ,0  part 1/1 <<-- garbled data (can't be decoded)
    sector 013: chunk 1 ,0  part 1/1
    sector 014: chunk 4 ,0  part 1/3 <<-- 1 sector required, but 3 sectors allocated
    sector 015: chunk 12,0  part 1/1 <<-- part 2 of chunk 4,0 overlaps
    sector 016: chunk 4, 0  part 3/3
    sector 017: chunk 16,0  part 1/2
    sector 018: chunk 16,0  part 2/2
    sector 019: chunk 5 ,1  part 1/2 <<-- correct encoding, but not a valid NBT file
    sector 020: chunk 5 ,1  part 2/2
    sector 021: chunk 6 ,1  part 1/1 <<-- potential overlap with empty chunk 13,0
    sector 022: chunk 7 ,1  part 1/1 <<-- no timestamp
    sector 023: chunk 4 ,1  part 1/1 <<-- zero-byte length value in chunk (invalid header)
    sector 024: chunk 8 ,1  part 1/1 <<-- one-byte length value in chunk (no data)
    sector 025: chunk 3 ,1  part 1/1 <<-- 2 sectors required, but 1 sector allocated (length 4+1+4092)
    sector 026: empty                <<-- unregistered overlap from chunk 3,1
    
    in addition, the following (corrupted) chunks are defined in the header of regiontest.mca:
    sector 021: 0-sector length chunk 13,0 (and overlapping with chunk 6,1)
    sector 001: chunk 14,0 (in header)
    sector 030: chunk 15,0 (out of file)
    ----------: chunk 17,0 timestamp without data
    
    Thus:
    01. chunk 1 ,0  Readable  
    02. chunk 2 ,0  Readable   <<-- uncompressed (encoding 0)
    03. chunk 3 ,0  Unreadable <<-- garbled data (can't be decoded)
    04. chunk 4 ,0  Readable   <<-- overlaps with chunk 12,0.
    05. chunk 6 ,0  Readable 
    06. chunk 7 ,0  Readable 
    07. chunk 8 ,0  Readable 
    08. chunk 9 ,0  Readable 
    09. chunk 10,0  Readable   <<-- deprecated encoding (gzip = 1)
    10. chunk 11,0  Unreadable <<-- unknown encoding (3)
    11. chunk 12,0  Readable   <<-- Overlaps with chunk 4,0.
    12. chunk 13,0  Unreadable <<-- 0-sector length in header
    13. chunk 14,0  Unreadable <<-- in header
    14. chunk 15,0  Unreadable <<-- out of file
    15. chunk 16,0  Readable  
    --  chunk 17,0  Unreadable <<-- timestamp without data
    16. chunk 3 ,1  Readable   <<-- 2 sectors required, but 1 sector allocated (length 4+1+4092)
    17. chunk 4 ,1  Unreadable <<-- zero-byte length value in chunk (invalid header)
    18. chunk 5 ,1  Readable   <<-- Not a valid NBT file
    19. chunk 6 ,1  Readable   <<-- potential overlap with empty chunk 13,0
    20. chunk 7 ,1  Readable   <<-- no timestamp
    21. chunk 8 ,1  Unreadable <<-- one-byte length value in chunk (no data)
    """

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = os.path.join(self.tempdir, 'regiontest.mca')
        shutil.copy(REGIONTESTFILE, self.filename)
        self.region = RegionFile(filename = self.filename)

    def tearDown(self):
        del self.region
        try:
            shutil.rmtree(self.tempdir)
        except OSError as e:
            raise

    def test000MethodFileSize(self):
        """
        Test of the get_size() method.
        The regionfile has 27 sectors.
        """
        self.assertEqual(self.region.get_size(), 27*4096)

    def test001MethodChunkCount(self):
        """
        Test of the chunk_count() method.
        The regionfile has 21 chunks, including 3-out of file chunks.
        """
        self.assertEqual(self.region.chunk_count(), 21)

    def test002MethodGetChunkCoords(self):
        """
        Test of get_chunk_coords() method.
        Note: this function may be deprecated in a later version of NBT.
        """
        coords_and_lengths = self.region.get_chunk_coords()
        coords = []
        for coord in coords_and_lengths:
            coords.append((coord['x'], coord['z']))
        
        self.assertIn((1, 0), coords)
        self.assertIn((2, 0), coords)
        self.assertIn((3, 0), coords)
        self.assertIn((4, 0), coords)
        self.assertIn((6, 0), coords)
        self.assertIn((7, 0), coords)
        self.assertIn((8, 0), coords)
        self.assertIn((9, 0), coords)
        self.assertIn((10, 0), coords)
        self.assertIn((11, 0), coords)
        self.assertIn((12, 0), coords)
        self.assertIn((13, 0), coords)
        self.assertIn((14, 0), coords) # note: length is undefined
        self.assertIn((15, 0), coords) # note: length is undefined
        self.assertIn((16, 0), coords)
        self.assertNotIn((17, 0), coords)
        self.assertIn((3, 1), coords)
        self.assertIn((4, 1), coords)
        self.assertIn((5, 1), coords)
        self.assertIn((6, 1), coords)
        self.assertIn((7, 1), coords)
        self.assertIn((8, 1), coords)
        self.assertEqual(len(coords_and_lengths), 21)

    def test003MethodIterChunks(self):
        """
        Test of iter_chunks() method.
        """
        chunks = []
        for chunk in self.region.iter_chunks():
            self.assertIsInstance(chunk, TAG_Compound)
            chunks.append(chunk)
        self.assertEqual(len(chunks), 13)

    def test004SyntaxIterChunks(self):
        """
        Test of iter(RegionFile) syntax.
        """
        chunks = []
        for chunk in self.region:
            self.assertIsInstance(chunk, TAG_Compound)
            chunks.append(chunk)
        self.assertEqual(len(chunks), 13)
    
    def test005ParameterHeaders(self):
        """
        read headers of chunk 9,0: 
        sector 6, 1 sector length, timestamp 1334530101, status STATUS_CHUNK_OK.
        read chunk headers of chunk 9,0: 
        length (incl. compression byte): 3969 bytes, zlip (2) compression, status STATUS_CHUNK_OK.
        """
        self.assertEqual(self.region.header[9,0], (6, 1, 1334530101, RegionFile.STATUS_CHUNK_OK))
        self.assertEqual(self.region.chunk_headers[9,0], (3969, 2, RegionFile.STATUS_CHUNK_OK))
    
    def test006ParameterHeadersUndefinedChunk(self):
        """
        read headers & chunk_headers of chunk 2,2
        """
        self.assertEqual(self.region.header[2,2], (0, 0, 0, RegionFile.STATUS_CHUNK_NOT_CREATED))
        self.assertEqual(self.region.chunk_headers[2,2], \
                        (None, None, RegionFile.STATUS_CHUNK_NOT_CREATED))
    
    def test010ReadChunkZlibCompression(self):
        """
        chunk 9,0: regular Zlib compression. Should be read OK.
        """
        nbt = self.region.get_nbt(9, 0)
        self.assertIsInstance(nbt, TAG_Compound)
        # get_chunk is currently an alias of get_nbt
        chunk = self.region.get_chunk(9, 0)
        self.assertIsInstance(chunk, TAG_Compound)

    def test011ReadChunkGzipCompression(self):
        """
        chunk 10,0: deprecated GZip compression. Should be read OK.
        """
        nbt = self.region.get_nbt(10, 0)
        self.assertIsInstance(nbt, TAG_Compound)

    def test012ReadChunkUncompressed(self):
        """
        chunk 2,0: no compression. Should be read OK.
        """
        nbt = self.region.get_nbt(2, 0)
        self.assertIsInstance(nbt, TAG_Compound)

    def test013ReadUnknownEncoding(self):
        """
        chunk 11,0 has unknown encoding (3). Reading should raise a ChunkDataError.
        """
        self.assertRaises(ChunkDataError, self.region.get_nbt, 11, 0)

    def test014ReadMalformedEncoding(self):
        """
        chunk 3,0 has malformed content. Reading should raise a ChunkDataError.
        This should not raise a MalformedFileError.
        """
        self.assertRaises(ChunkDataError, self.region.get_nbt, 3, 0)

    def test015ReadMalformedNBT(self):
        """
        read chunk 5,1: valid compression, but not a valid NBT file. 
        Reading should raise a ChunkDataError, not a nbt.nbt.MalformedFileError.
        """
        self.assertRaises(ChunkDataError, self.region.get_nbt, 5, 1)

    def test016ReadChunkNonExistent(self):
        """
        read chunk 2,2: does not exist. Reading should raise a InconceivedChunk.
        """
        self.assertRaises(InconceivedChunk, self.region.get_nbt, 2, 2)

    def test017ReadableChunks(self):
        """
        Test which chunks are readable.
        """
        coords = []
        for cc in self.region.get_chunk_coords():
            try:
                nbt = self.region.get_chunk(cc['x'], cc['z'])
                coords.append((cc['x'], cc['z']))
            except RegionFileFormatError:
                pass

        self.assertIn((1, 0), coords)
        self.assertIn((2, 0), coords)
        self.assertNotIn((3, 0), coords) # garbled data
        self.assertIn((4, 0), coords) # readable, despite overlapping with chunk 12,0
        self.assertIn((6, 0), coords)
        self.assertIn((7, 0), coords)
        self.assertIn((8, 0), coords)
        self.assertIn((9, 0), coords)
        self.assertIn((10, 0), coords)
        self.assertNotIn((11, 0), coords) # unknown encoding
        self.assertIn((12, 0), coords) # readable, despite overlapping with chunk 4,1
        self.assertNotIn((13, 0), coords) # zero-length (in header)
        self.assertNotIn((14, 0), coords) # in header
        self.assertNotIn((15, 0), coords) # out of file
        self.assertIn((16, 0), coords)
        self.assertNotIn((17, 0), coords) # timestamp without data
        self.assertIn((3, 1), coords)
        self.assertNotIn((4, 1), coords) # invalid length (in chunk)
        self.assertNotIn((5, 1), coords) # not a valid NBT file
        self.assertIn((6, 1), coords)
        self.assertIn((7, 1), coords)
        self.assertNotIn((8, 1), coords) # zero-length (in chunk)
        self.assertEqual(len(coords), 13)

    def test020ReadInHeader(self):
        """
        read chunk 14,0: supposedly located in the header. 
        Reading should raise a RegionHeaderError.
        """
        self.assertRaises(RegionHeaderError, self.region.get_nbt, 14, 0)
        self.assertEqual(self.region.header[14,0], 
                         (1, 1, 1376433960, RegionFile.STATUS_CHUNK_IN_HEADER))
        self.assertEqual(self.region.chunk_headers[14,0], 
                         (None, None, RegionFile.STATUS_CHUNK_IN_HEADER))

    def test021ReadOutOfFile(self):
        """
        read chunk 15,0: error (out of file)
        """
        self.assertRaises(RegionHeaderError, self.region.get_nbt, 15, 0)
        self.assertEqual(self.region.header[15,0], 
                         (30, 1, 1376433961, RegionFile.STATUS_CHUNK_OUT_OF_FILE))
        self.assertEqual(self.region.chunk_headers[15,0], 
                         (None, None, RegionFile.STATUS_CHUNK_OUT_OF_FILE))

    def test022ReadZeroLengthHeader(self):
        """
        read chunk 13,0: error (zero-length)
        """
        self.assertRaises(RegionHeaderError, self.region.get_nbt, 13, 0)
        self.assertEqual(self.region.header[13,0], 
                         (21, 0, 1376433958, RegionFile.STATUS_CHUNK_ZERO_LENGTH))
        self.assertEqual(self.region.chunk_headers[13,0],
                         (None, None, RegionFile.STATUS_CHUNK_ZERO_LENGTH))

    def test023ReadInvalidLengthChunk(self):
        """
        zero-byte lengths in chunk. (4,1)
        read chunk 4,1: error (invalid)
        """
        self.assertRaises(ChunkHeaderError, self.region.get_nbt, 4, 1)

    def test024ReadZeroLengthChunk(self):
        """
        read chunk 8,1: error (zero-length chunk)
        """
        self.assertRaises(ChunkHeaderError, self.region.get_nbt, 8, 1)

    def test025ReadChunkSizeExceedsSectorSize(self):
        """
        read chunk 3,1: can be read, despite that the chunk content is longer 
        than the allocated sectors.
        In general, reading should either succeeds, or raises a ChunkDataError.
        The status should be STATUS_CHUNK_MISMATCHED_LENGTHS.
        """
        self.assertEqual(self.region.chunk_headers[3,1][2], 
                         RegionFile.STATUS_CHUNK_MISMATCHED_LENGTHS)
        # reading should succeed, despite the overlap (next chunk is free)
        nbt = self.region.get_nbt(3, 1)

    def test026ReadChunkOverlapping(self):
        """
        chunk 4,0 and chunk 12,0 overlap: status should be STATUS_CHUNK_OVERLAPPING
        """
        self.assertEqual(self.region.chunk_headers[4,0][2], 
                         RegionFile.STATUS_CHUNK_OVERLAPPING)
        self.assertEqual(self.region.chunk_headers[12,0][2], 
                         RegionFile.STATUS_CHUNK_OVERLAPPING)

    def test030GetTimestampOK(self):
        """
        get_timestamp
        read chunk 9,0: OK
        """
        self.assertEqual(self.region.get_timestamp(9,0), 1334530101)

    def test031GetTimestampBadChunk(self):
        """
        read chunk 15,0: OK
        Data is out-out-of-file, but timestamp is still there.
        """
        self.assertEqual(self.region.get_timestamp(15,0), 1376433961)

    def test032GetTimestampNoChunk(self):
        """
        read chunk 17,0: OK
        no data, but a timestamp
        """
        self.assertEqual(self.region.get_timestamp(17,0), 1334530101)

    def test033GetTimestampMissing(self):
        """
        read chunk 7,1: OK
        data, but no timestamp
        """
        self.assertEqual(self.region.get_timestamp(7,1), 0)

    def test040WriteNewChunk(self):
        """
        read chunk 0,2: InconceivedError
        write 1 sector chunk 0,2
        - read location (<= 026), size (001), timestamp (non-zero).
        """
        chunk_count = self.region.chunk_count()
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.assertRaises(InconceivedChunk, self.region.get_nbt, 0, 2)
        timebefore = int(time.time())
        self.region.write_chunk(0, 2, nbt)
        timeafter = time.time()
        header = self.region.header[0,2]
        self.assertEqual(header[1], 1, "Chunk length must be 1 sector")
        self.assertGreaterEqual(header[0], 2, "Chunk must not be written in the header")
        self.assertLessEqual(header[0], 26, "Chunk must not be written in an empty sector")
        self.assertGreaterEqual(header[2], timebefore, "Timestamp must be time.time()")
        self.assertLessEqual(header[2], timeafter, "Timestamp must be time.time()")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)
        self.assertEqual(self.region.chunk_count(), chunk_count + 1)

    def test041WriteAndReadNewChunk(self):
        """
        write 1 sector chunk 0,2
        read chunk 0,2: OK
        - compare writen and read NBT file
        """
        nbtwrite = generate_compressed_level(minsize = 100, maxsize = 4000)
        writebuffer = BytesIO()
        nbtwrite.write_file(buffer=writebuffer)
        nbtsize = writebuffer.seek(0,2)
        self.region.write_chunk(0, 2, nbtwrite)
        nbtread = self.region.get_nbt(0, 2)
        readbuffer = BytesIO()
        nbtread.write_file(buffer=readbuffer)
        self.assertEqual(nbtsize, readbuffer.seek(0,2))
        writebuffer.seek(0)
        writtendata = writebuffer.read()
        readbuffer.seek(0)
        readdata = readbuffer.read()
        self.assertEqual(writtendata, readdata)

    def test042WriteExistingChunk(self):
        """
        write 1 sector chunk 9,0 (should stay in 006)
        - read location (006) and size (001).
        """
        chunk_count = self.region.chunk_count()
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(9, 0, nbt)
        header = self.region.header[9, 0]
        self.assertEqual(header[0], 6, "Chunk should remain at sector 6")
        self.assertEqual(header[1], 1, "Chunk length must be 1 sector")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)
        self.assertEqual(self.region.chunk_count(), chunk_count)

    def test043DeleteChunk(self):
        """
        read chunk 6,0: OK
        unlink chunk 6,0
        - check location, size, timestamp (all should be 0)
        read chunk 6,0: InconceivedError
        """
        chunk_count = self.region.chunk_count()
        nbt = self.region.get_nbt(6, 0)
        self.region.unlink_chunk(6, 0)
        self.assertRaises(InconceivedChunk, self.region.get_nbt, 6, 0)
        header = self.region.header[6, 0]
        self.assertEqual(header[0], 0)
        self.assertEqual(header[1], 0)
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_NOT_CREATED)
        self.assertEqual(self.region.chunk_count(), chunk_count - 1)

    def test044UseEmptyChunks(self):
        """
        write 1 sector chunk 1,2 (should go to 004)
        write 1 sector chunk 2,2 (should go to 010)
        write 1 sector chunk 3,2 (should go to 011)
        verify file size remains 027*4096
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        availablelocations = (4, 10, 11, 26)
        self.region.write_chunk(1, 2, nbt)
        self.assertIn(self.region.header[1, 2][0], availablelocations)
        self.region.write_chunk(2, 2, nbt)
        self.assertIn(self.region.header[2, 2][0], availablelocations)
        self.region.write_chunk(3, 2, nbt)
        self.assertIn(self.region.header[3, 2][0], availablelocations)

    def test050WriteNewChunk2sector(self):
        """
        write 2 sector chunk 1,2 (should go to 010-011)
        """
        nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
        self.region.write_chunk(1, 2, nbt)
        header = self.region.header[1, 2]
        self.assertEqual(header[1], 2, "Chunk length must be 2 sectors")
        self.assertEqual(header[0], 10, "Chunk should be placed in sector 10")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)

    def test051WriteNewChunk4096byte(self):
        """
        write 4091+5-byte (1 sector) chunk 1,2 (should go to 004)
        """
        nbt = generate_compressed_level(minsize = 4091, maxsize = 4091)
        self.region.write_chunk(1, 2, nbt)
        header = self.region.header[1, 2]
        chunk_header = self.region.chunk_headers[1, 2]
        if chunk_header[0] != 4092:
            raise unittest.SkipTest("Can't create chunk of 4091 bytes compressed")
        self.assertEqual(header[1], 1, "Chunk length must be 2 sectors")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)

    def test052WriteNewChunk4097byte(self):
        """
        write 4092+5-byte (2 sector) chunk 1,2 (should go to 010-011)
        """
        nbt = generate_compressed_level(minsize = 4092, maxsize = 4092)
        self.region.write_chunk(1, 2, nbt)
        header = self.region.header[1, 2]
        chunk_header = self.region.chunk_headers[1, 2]
        if chunk_header[0] != 4093:
            raise unittest.SkipTest("Can't create chunk of 4092 bytes compressed")
        self.assertEqual(header[1], 2, "Chunk length must be 2 sectors")
        self.assertEqual(header[0], 10, "Chunk should be placed in sector 10")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)

    def test053WriteNewChunkIncreaseFile(self):
        """
        write 3 sector chunk 2,2 (should go to 026-028 or 027-029) (increase file size)
        verify file size is 29*4096
        """
        nbt = generate_compressed_level(minsize = 9000, maxsize = 11000)
        self.region.write_chunk(1, 2, nbt)
        header = self.region.header[1, 2]
        self.assertEqual(header[1], 3, "Chunk length must be 3 sectors")
        self.assertIn(header[0], (26, 27), "Chunk should be placed in sector 26")
        self.assertEqual(self.region.get_size(), (header[0] + header[1])*4096, \
                         "File size should be multiple of 4096")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)

    def test054WriteExistingChunkDecreaseSector(self):
        """
        write 1 sector chunk 16,0 (should go to existing 017) (should free sector 018)
        write 1 sector chunk 1,2 (should go to 004)
        write 1 sector chunk 2,2 (should go to 010)
        write 1 sector chunk 3,2 (should go to 011)
        write 1 sector chunk 4,2 (should go to freed 018)
        write 1 sector chunk 5,2 (should go to 026)
        verify file size remains 027*4096
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        header = self.region.header[16, 0]
        self.assertEqual(header[1], 2)
        self.region.write_chunk(16, 0, nbt)
        header = self.region.header[16, 0]
        self.assertEqual(header[1], 1, "Chunk length must be 1 sector1")
        self.assertEqual(header[0], 17, "Chunk should remain in sector 17")
        # Write 1-sector chunks to check which sectors are "free"
        locations = []
        self.region.write_chunk(1, 2, nbt)
        locations.append(self.region.header[1, 2][0])
        self.region.write_chunk(2, 2, nbt)
        locations.append(self.region.header[2, 2][0])
        self.region.write_chunk(3, 2, nbt)
        locations.append(self.region.header[3, 2][0])
        self.region.write_chunk(4, 2, nbt)
        locations.append(self.region.header[4, 2][0])
        self.region.write_chunk(5, 2, nbt)
        locations.append(self.region.header[5, 2][0])
        self.assertIn(18, locations)
        # self.assertEqual(locations, [4, 10, 11, 18, 26])
        # self.assertEqual(self.region.get_size(), 27*4096)

    @unittest.skip('Test takes too much time')
    def test055WriteChunkTooLarge(self):
        """
        Chunks of size >= 256 sectors are not supported by the file format
        attempt to write a chunk 256 sectors in size
        should raise Exception
        """
        maxsize = 256 * 4096
        nbt = generate_compressed_level(minsize = maxsize + 100, maxsize = maxsize + 4000)
        self.assertRaises(ChunkDataError, self.region.write_chunk, 2, 2, nbt)

    def test060WriteExistingChunkIncreaseSectorSameLocation(self):
        """
        write 2 sector chunk 7,0 (should go to 003-004) (increase chunk size)
        """
        nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
        self.region.write_chunk(7, 0, nbt)
        header = self.region.header[7, 0]
        self.assertEqual(header[1], 2, "Chunk length must be 2 sectors")
        self.assertEqual(header[0], 3, "Chunk should remain in sector 3")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)
        # self.assertEqual(self.region.get_size(), 27*4096)

    def test061WriteExistingChunkCorrectSize(self):
        """
        write 2 sector chunk 3,1 (should go to 025-026) (increase sector size)
        """
        nbt = self.region.get_chunk(3, 1)
        self.region.write_chunk(3, 1, nbt)
        header = self.region.header[3, 1]
        self.assertEqual(header[1], 2, "Chunk length must be 2 sectors")
        self.assertEqual(header[0], 25, "Chunk should remain in sector 25")
        self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)
        self.assertEqual(self.region.get_size(), 27*4096)

    def test062WriteExistingChunkIncreaseSectorNewLocation(self):
        """
        write 2 sector chunk 8,0 (should go to 004-005 or 010-011)
        verify chunk_count remains 18
        write 2 sector chunk 2,2 (should go to 010-011 or 004-005)
        verify that file size is not increased <= 027*4096
        verify chunk_count is 19
        """
        locations = []
        chunk_count = self.region.chunk_count()
        nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
        self.region.write_chunk(8, 0, nbt)
        header = self.region.header[8, 0]
        self.assertEqual(header[1], 2) # length
        locations.append(header[0]) # location
        self.assertEqual(self.region.chunk_count(), chunk_count)
        self.region.write_chunk(2, 2, nbt)
        header = self.region.header[2, 2]
        self.assertEqual(header[1], 2) # length
        locations.append(header[0]) # location
        self.assertEqual(sorted(locations), [4, 10]) # locations
        self.assertEqual(self.region.chunk_count(), chunk_count + 1)

    def test063WriteNewChunkFreedSectors(self):
        """
        unlink chunk 6,0
        unlink chunk 7,0
        write 3 sector chunk 2,2 (should go to 002-004) (file size should remain the same)
        """
        self.region.unlink_chunk(6, 0)
        self.region.unlink_chunk(7, 0)
        nbt = generate_compressed_level(minsize = 9000, maxsize = 11000)
        self.region.write_chunk(2, 2, nbt)
        header = self.region.header[2, 2]
        self.assertEqual(header[1], 3, "Chunk length must be 3 sectors")
        self.assertEqual(header[0], 2, "Chunk should be placed in sector 2")

    # TODO: test write_blockdata, with different compressions. Check the metadata. Read the data back.

    def test070WriteOutOfFileChunk(self):
        """
        write 1 sector chunk 13,0 (should go to 004)
        Should not go to sector 30 (out-of-file location)
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(13, 0, nbt)
        header = self.region.header[13, 0]
        self.assertEqual(header[1], 1) # length
        self.assertLessEqual(header[0], 26, \
                "Previously out-of-file chunk should be written in-file")

    def test071WriteZeroLengthSectorChunk(self):
        """
        write 1 sector chunk 13,0 (should go to 004)
        Verify sector 19 remains untouched.
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(13, 0, nbt)
        header = self.region.header[13, 0]
        self.assertEqual(header[1], 1) # length
        self.assertNotEqual(header[0], 19, \
                "Previously 0-length chunk should not overwrite existing chunk")

    def test072WriteOverlappingChunkLong(self):
        """
        write 2 sector chunk 4,0 (should go to 010-011) (free 014 & 016)
        verify location is NOT 014 (because of overlap)
        write 1 sector chunk 1,2 (should go to 004)
        write 1 sector chunk 2,2 (should go to freed 014)
        write 1 sector chunk 3,2 (should go to freed 016)
        write 1 sector chunk 4,2 (should go to 018)
        write 1 sector chunk 5,2 (should go to 026)
        verify file size remains 027*4096
        """
        nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
        self.region.write_chunk(4, 0, nbt)
        header = self.region.header[4, 0]
        self.assertEqual(header[1], 2) # length
        self.assertNotEqual(header[0], 14, \
                "Chunk should not be written to same location when it overlaps")
        self.assertEqual(header[0], 10, \
                "Chunk should not be written to same location when it overlaps")
        # Write 1-sector chunks to check which sectors are "free"
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        locations = []
        self.region.write_chunk(1, 2, nbt)
        locations.append(self.region.header[1, 2][0])
        self.region.write_chunk(2, 2, nbt)
        locations.append(self.region.header[2, 2][0])
        self.region.write_chunk(3, 2, nbt)
        locations.append(self.region.header[3, 2][0])
        self.region.write_chunk(4, 2, nbt)
        locations.append(self.region.header[4, 2][0])
        self.region.write_chunk(5, 2, nbt)
        locations.append(self.region.header[5, 2][0])
        self.assertIn(14, locations)
        self.assertIn(16, locations)
        # self.assertEqual(locations, [4, 14, 16, 18, 26])
        # self.assertEqual(self.region.get_size(), 27*4096)

    def test073WriteOverlappingChunkSmall(self):
        """
        write 1 sector chunk 12,0 (should go to 004) ("free" 015 for use by 4,0)
        verify location is NOT 015
        verify sectors 15 and 16 are not marked as "free", but remain in use by 4,0
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(12, 0, nbt)
        header = self.region.header[12, 0]
        self.assertEqual(header[1], 1) # length
        self.assertNotEqual(header[0], 15, \
                "Chunk should not be written to same location when it overlaps")
        # Write 1-sector chunks to check which sectors are "free"
        locations = []
        self.region.write_chunk(1, 2, nbt)
        locations.append(self.region.header[1, 2][0])
        self.region.write_chunk(2, 2, nbt)
        locations.append(self.region.header[2, 2][0])
        self.region.write_chunk(3, 2, nbt)
        locations.append(self.region.header[3, 2][0])
        self.assertNotIn(15, locations)
        self.assertNotIn(16, locations)
        # self.assertEqual(locations, [10, 11, 26])
        # self.assertEqual(self.region.get_size(), 27*4096)

    def test074WriteOverlappingChunkSameLocation(self):
        """
        write 1 sector chunk 12,0 (should go to 004) ("free" 012 for use by 4,0)
        write 3 sector chunk 4,0 (should stay in 014-016)
        verify file size remains <= 027*4096
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(12, 0, nbt)
        header = self.region.header[12, 0]
        self.assertEqual(header[1], 1) # length
        self.assertNotEqual(header[0], 15, \
                "Chunk should not be written to same location when it overlaps")
        nbt = generate_compressed_level(minsize = 9000, maxsize = 11000)
        self.region.write_chunk(4, 0, nbt)
        header = self.region.header[4, 0]
        self.assertEqual(header[1], 3) # length
        self.assertEqual(header[0], 14, "No longer overlapping chunks " + \
                "should be written to same location when when possible")

    def test080FileTruncateLastChunkDecrease(self):
        """
        write 1 sector chunk 3,1 (should remain in 025) (free 026)
        verify file size is truncated: 26*4096 bytes
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(3, 1, nbt)
        self.assertEqual(self.region.get_size(), 26*4096, \
                "File should be truncated when last chunk is reduced in size")

    def test081FileTruncateFreeTail(self):
        """
        delete chunk 3,1 (free 025: truncate file size)
        verify file size: 25*4096 bytes
        """
        self.region.unlink_chunk(3, 1)
        self.assertEqual(self.region.get_size(), 25*4096, \
                "File should be truncated when last sector(s) are freed")

    def test082FileTruncateMergeFree(self):
        """
        delete chunk 8,1 (free 024)
        delete chunk 3,1 (free 025: truncate file size, including 024)
        verify file size: 24*4096 bytes
        """
        self.region.unlink_chunk(8, 1)
        self.region.unlink_chunk(3, 1)
        self.assertEqual(self.region.get_size(), 24*4096, "File should be " + \
                "truncated as far as possible when last sector(s) are freed")

    def test090DeleteNonExistingChunk(self):
        """
        delete chunk 2,2
        """
        self.region.unlink_chunk(2, 2)
        self.assertFalse(self.region.metadata[2, 2].is_created())

    def test091DeleteNonInHeaderChunk(self):
        """
        delete chunk 14,0. This should leave sector 1 untouched.
        verify sector 1 is unmodified, with the exception of timestamp for chunk 14,0.
        """
        self.region.file.seek(4096)
        before = self.region.file.read(4096)
        chunklocation = 4 * (14 + 32*1)
        before = before[:chunklocation] + before[chunklocation+4:]
        self.region.unlink_chunk(14, 1)
        self.region.file.seek(4096)
        after = self.region.file.read(4096)
        after = after[:chunklocation] + after[chunklocation+4:]
        self.assertEqual(before, after)

    def test092DeleteOutOfFileChunk(self):
        """
        delete chunk 15,1
        verify file size is not increased.
        """
        size = self.region.get_size()
        self.region.unlink_chunk(15, 1)
        self.assertLessEqual(self.region.get_size(), size)

    def test093DeleteChunkZeroTimestamp(self):
        """
        delete chunk 17,0
        verify timestamp is zeroed. both in get_timestamp() and get_metadata()
        """
        self.assertEqual(self.region.get_timestamp(17, 0), 1334530101)
        self.region.unlink_chunk(17, 0)
        self.assertEqual(self.region.get_timestamp(17, 0), 0)

    def test100WriteZeroPadding(self):
        """
        write 1 sector chunk 16,0 (should go to existing 017) (should free sector 018)
        Check if unused bytes in sector 017 and all bytes in sector 018 are zeroed.
        """
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(16, 0, nbt)
        header = self.region.header[16, 0]
        chunk_header = self.region.chunk_headers[16, 0]
        sectorlocation = header[0]
        oldsectorlength = 2 * 4096
        chunklength = 4 + chunk_header[0]
        unusedlength = oldsectorlength - chunklength
        self.region.file.seek(4096*sectorlocation + chunklength)
        unused = self.region.file.read(unusedlength)
        zeroes = unused.count(b'\x00')
        self.assertEqual(zeroes, unusedlength, \
                "All unused bytes should be zeroed after writing a chunk")
    
    def test101DeleteZeroPadding(self):
        """
        unlink chunk 7,1
        Check if all bytes in sector 022 are zeroed.
        """
        header = self.region.header[7, 1]
        sectorlocation = header[0]
        self.region.unlink_chunk(7, 1)
        self.region.file.seek(sectorlocation*4096)
        unused = self.region.file.read(4096)
        zeroes = unused.count(b'\x00')
        self.assertEqual(zeroes, 4096, "All bytes should be zeroed after deleting a chunk")
    
    def test102DeleteOverlappingNoZeroPadding(self):
        """
        unlink chunk 4,0. Due to overlapping chunks, bytes should not be zeroed.
        Check if bytes in sector 015 are not all zeroed.
        """
        header = self.region.header[4, 0]
        sectorlocation = header[0]
        self.region.unlink_chunk(4, 0)
        self.region.file.seek((sectorlocation + 1) * 4096)
        unused = self.region.file.read(4096)
        zeroes = unused.count(b'\x00')
        self.assertNotEqual(zeroes, 4096, \
                "Bytes should not be zeroed after deleting an overlapping chunk")
        self.region.file.seek((sectorlocation) * 4096)
        unused = self.region.file.read(4096)
        zeroes = unused.count(b'\x00')
        self.assertEqual(zeroes, 4096, "Bytes should be " + \
                "zeroed after deleting non-overlapping portions of a chunk")
        self.region.file.seek((sectorlocation + 2) * 4096)
        unused = self.region.file.read(4096)
        zeroes = unused.count(b'\x00')
        self.assertEqual(zeroes, 4096, "Bytes should be " + \
                "zeroed after deleting non-overlapping portions of a chunk")
    
    def test103MoveOverlappingNoZeroPadding(self):
        """
        write 2 sector chunk 4,0 to a different location. 
        Due to overlapping chunks, bytes should not be zeroed.
        Check if bytes in sector 015 are not all zeroed.
        """
        header = self.region.header[4, 0]
        sectorlocation = header[0]
        nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
        self.region.write_chunk(4, 0, nbt)
        self.region.file.seek((sectorlocation + 1) * 4096)
        unused = self.region.file.read(4096)
        zeroes = unused.count(b'\x00')
        self.assertNotEqual(zeroes, 4096, \
                "Bytes should not be zeroed after moving an overlapping chunk")
    
    def test104DeleteZeroPaddingMismatchLength(self):
        """
        unlink chunk 3,1. (which has a length mismatch)
        Check if bytes in sector 025 are all zeroed.
        Check if first byte in sector 026 is not zeroed.
        """
        raise unittest.SkipTest("Test can't use this testfile")
        # TODO: Why not? Create other test file



class EmptyFileTest(unittest.TestCase):
    """Test for 0-byte file support.
    These files should be treated as a valid region file without any stored chunk."""
    
    @staticmethod
    def generate_level():
        level = NBTFile() # Blank NBT
        level.name = "Data"
        level.tags.extend([
            TAG_Long(name="Time", value=1),
            TAG_Long(name="LastPlayed", value=1376031942),
            TAG_Int(name="SpawnX", value=0),
            TAG_Int(name="SpawnY", value=2),
            TAG_Int(name="SpawnZ", value=0),
            TAG_Long(name="SizeOnDisk", value=0),
            TAG_Long(name="RandomSeed", value=123456789),
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
        return level

    def setUp(self):
        self.stream = PedanticFileWrapper(BytesIO(b""))
        # self.stream.seek(0)

    def test01ReadFile(self):
        region = RegionFile(fileobj=self.stream)
        self.assertEqual(region.chunk_count(), 0)

    def test02WriteFile(self):
        chunk = self.generate_level()
        region = RegionFile(fileobj=self.stream)
        region.write_chunk(0, 0, chunk)
        self.assertEqual(region.get_size(), 3*4096)
        self.assertEqual(region.chunk_count(), 1)

class RegionFileInitTest(unittest.TestCase):
    """Tests for the various init parameters provided for RegionFile()."""
    
    def testCreateFromFilename(self):
        """
        Creating a RegionFile with filename, and deleting the instance should 
        close the underlying file.
        """
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, 'regiontest.mca')
        shutil.copy(REGIONTESTFILE, filename)
        try:
            openfiles_before = open_files()
        except OSError:
            raise unittest.SkipTest("Can't get a list of open files")
        region = RegionFile(filename = filename)
        openfiles_during = open_files()
        del region
        openfiles_after = open_files()
        
        self.assertNotEqual(len(openfiles_during), 0)
        self.assertNotEqual(openfiles_before, openfiles_during)
        self.assertEqual(openfiles_before, openfiles_after, "File is not closed")

    def testCreateFromFileobject(self):
        """
        Creating RegionFile with file object, and deleting the instance should 
        not close the underlying file.
        """
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, 'regiontest.mca')
        shutil.copy(REGIONTESTFILE, filename)
        fileobj = open(filename, "r+b")
        
        try:
            openfiles_before = open_files()
        except OSError:
            raise unittest.SkipTest("Can't get a list of open files")
        region = RegionFile(fileobj = fileobj)
        openfiles_during = open_files()
        del region
        openfiles_after = open_files()
        
        fileobj.close()

        self.assertNotEqual(len(openfiles_during), 0)
        self.assertEqual(openfiles_before, openfiles_during)
        self.assertEqual(openfiles_before, openfiles_after, \
                "File is closed, while it should remain open")

    def testNoParameters(self):
        """Calling RegionFile without parameters should raise a ValueError"""
        # Equivalent to: region = RegionFile()
        self.assertRaises(ValueError, RegionFile)

    def testTwoParameters(self):
        """Calling RegionFile with both filename and fileobject should ignore the fileobject."""
        tempdir = tempfile.mkdtemp()
        filename_name = os.path.join(tempdir, 'regiontest_name.mca')
        shutil.copy(REGIONTESTFILE, filename_name)
        filename_obj = os.path.join(tempdir, 'regiontest_obj.mca')
        shutil.copy(REGIONTESTFILE, filename_obj)
        fileobj = open(filename_obj, "r+b")
        
        try:
            openfiles_before = open_files()
        except OSError:
            raise unittest.SkipTest("Can't get a list of open files")
        region = RegionFile(filename = filename_name, fileobj = fileobj)
        openfiles_during = open_files()
        self.assertEqual(region.filename, region.file.name)
        self.assertEqual(region.filename, filename_name)
        del region
        openfiles_after = open_files()
        
        fileobj.close()
        self.assertEqual(openfiles_before, openfiles_after)

    def testClosedStatus(self):
        """upon creation a region file shouldn't be closed.
        Calling `close()` should set the closed flag to true."""
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, 'regiontest.mca')
        shutil.copy(REGIONTESTFILE, filename)

        region = RegionFile(filename = filename)
        self.assertFalse(region.closed)
        region.close()
        self.assertTrue(region.closed)


# TODO: write tests
# class PartialHeaderFileTest(EmptyFileTest):
#   """Test for file support with only a partial header file.
#   These files should be treated as a valid region file without any stored chunk."""
#   
#   def setUp(self):
#       self.stream = BytesIO(4096*b"\x00" + b"\x52\x1E\x8B\xE6")
#       self.stream.seek(0)
# 
#   def test03GetTimestampNoChunk(self):
#       region = RegionFile(fileobj=self.stream)
#       self.assertEqual(region.get_timestamp(0,0), 1377733606)


class TruncatedFileTest(unittest.TestCase):
    """Test for truncated file support.
    This files should be treated as a valid region file, as all data is present.
    Only the padding bytes are missing."""

    def setUp(self):
        # data contains 8235, just over 2 sectors.
        # Only chunk (0,0) is stored, at sector 2, with length 1.
        # The timestamps are all zeroed.
        # The chunk is 0x27 = 39 bytes, excl header. Compression type 2, zlib.
        data = b'\x00\x00\x02\x01' + 8188*b'\x00' + \
               b'\x00\x00\x00\x27\x02' + \
               b'\x78\xda\xe3\x62\x60\x71\x49\x2c\x49\x64\x61\x60\x09\xc9' + \
               b'\xcc\x4d\x65\x80\x00\x46\x0e\x06\x16\xbf\x44\x20\x97\x25' + \
               b'\x24\xb5\xb8\x84\x01\x00\x6b\xb7\x06\x52'
        self.length = 8235 # 4096 + 4096 + 4 + 39
        self.assertEqual(len(data), self.length)
        stream = PedanticFileWrapper(BytesIO(data))
        # stream.seek(0)
        self.region = RegionFile(fileobj=stream)

    def tearDown(self):
        del self.region

    def test00FileProperties(self):
        self.assertEqual(self.region.get_size(), self.length)
        self.assertEqual(self.region.chunk_count(), 1)
    
    def test01ReadChunk(self):
        """Test if a block can be read, even when the file is truncated right 
        after the block data."""
        data = self.region.get_blockdata(0,0) # This may raise a RegionFileFormatError.
        data = BytesIO(data)
        nbt = NBTFile(buffer=data)
        self.assertEqual(nbt["Time"].value, 1)
        self.assertEqual(nbt["Name"].value, "Test")

    def test02ReplaceChunk(self):
        """Test if writing the last block in a truncated file will extend the 
        file size to the sector boundary."""
        nbt = self.region.get_nbt(0, 0)
        self.region.write_chunk(0, 0, nbt)
        size = self.region.size
        self.assertEqual(size, self.region.get_size())
        self.assertEqual(size, 3*4096)
    
    def test03WriteChunk(self):
        """Test if a new chunk extends the file to sector sizes."""
        nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
        self.region.write_chunk(0, 1, nbt)
        self.assertEqual(self.region.get_size(), 4*4096)
        self.assertEqual(self.region.size, 4*4096)
        self.assertEqual(self.region.chunk_count(), 2)
        self.region.file.seek(self.length)
        # The file length was extended to a block length.
        # Test if the padding contains zeroes.
        unusedlength = 3*4096 - self.length
        unused = self.region.file.read(unusedlength)
        zeroes = unused.count(b'\x00')
        self.assertEqual(unusedlength, zeroes)


class LengthTest(unittest.TestCase):
    """Test for length calculations for blocks with inconsistent lengths.
    
    This operates on a simple testfile with:
    file length: 4 sectors (00-03, inclusive)
    chunk 0,0: header length 4 sectors; chunk length 10240 bytes (3 sectors); sector 02-05
    chunk 1,0: header length 3 sectors; chunk length 613566756 bytes (149797 sectors); sector 03-149799
    """
    # max length value in header: 255 sectors = 1044480 bytes (1 MiByte)
    # max length value in chunk: 4294967295 bytes (4 GiBye) = 1048576 sectors
    def setUp(self):
        data = b'\x00\x00\x02\x04\x00\x00\x03\x03' + 8184*b'\x00' + \
               b'\x00\x00\x28\x00\x00' + 4091*b'\x01' + \
               b'\x24\x92\x49\x24\x00' + 4091*b'\x02'
        self.length = 16384
        self.assertEqual(len(data), self.length)
        stream = PedanticFileWrapper(BytesIO(data))
        # stream.seek(0)
        self.region = RegionFile(fileobj=stream)
    
    def tearDown(self):
        del self.region

    def test00FileProperties(self):
        self.assertEqual(self.region.get_size(), self.length)
        self.assertEqual(self.region.chunk_count(), 2)
    
    def testSectors(self):
        """Test if RegionFile._sectors() detects the correct overlap."""
        sectors = self.region._sectors()
        chunk00metadata = self.region.metadata[0,0]
        chunk10metadata = self.region.metadata[1,0]
        self.assertEqual(len(sectors), 4)
        self.assertEqual(sectors[0], True)
        self.assertEqual(sectors[1], True)
        self.assertEqual(len(sectors[2]), 1)
        self.assertIn(chunk00metadata, sectors[2])
        self.assertNotIn(chunk10metadata, sectors[2])
        self.assertEqual(len(sectors[3]), 2)
        self.assertIn(chunk00metadata, sectors[3])
        self.assertIn(chunk10metadata, sectors[3])
    
    def testMetaDataLengths(self):
        chunk00metadata = self.region.metadata[0,0]
        chunk10metadata = self.region.metadata[1,0]
        self.assertEqual(chunk00metadata.blocklength, 4)
        self.assertEqual(chunk00metadata.length, 10240)
        self.assertEqual(chunk10metadata.blocklength, 3)
        self.assertEqual(chunk10metadata.length, 613566756)
    
    def testMetaDataLengthCalculations(self):
        chunk00metadata = self.region.metadata[0,0]
        chunk10metadata = self.region.metadata[1,0]
        self.assertEqual(chunk00metadata.requiredblocks(), 3)
        self.assertEqual(chunk10metadata.requiredblocks(), 149797)
        
    def testMetaDataStatus(self):
        # performa low-level read, ensure it does not read past the file length
        # and does not modify the file
        chunk00metadata = self.region.metadata[0,0]
        chunk10metadata = self.region.metadata[1,0]
        self.assertIn(chunk00metadata.status, 
                    (RegionFile.STATUS_CHUNK_OVERLAPPING, 
                     RegionFile.STATUS_CHUNK_OUT_OF_FILE))
        self.assertIn(chunk10metadata.status, 
                    (RegionFile.STATUS_CHUNK_MISMATCHED_LENGTHS, 
                     RegionFile.STATUS_CHUNK_OVERLAPPING, 
                     RegionFile.STATUS_CHUNK_OUT_OF_FILE))
    
    def testChunkRead(self):
        """
        Perform a low-level read, ensure it does not read past the file length
        and does not modify the file.
        """
        # Does not raise a ChunkDataError(), since the data can be read, 
        # even though it is shorter than specified in the header.
        data = self.region.get_blockdata(0, 0)
        self.assertEqual(len(data), 8187)
        data = self.region.get_blockdata(1, 0)
        self.assertEqual(len(data), 4091)
        self.assertEqual(self.region.get_size(), self.length)
    
    def testDeleteChunk(self):
        """Try to remove the chunk 1,0 with ridiculous large size. 
        This should be reasonably fast."""
        self.region.unlink_chunk(1, 0)
        self.assertEqual(self.region.chunk_count(), 1)


# TODO: check if metadata is updated after deleting or writing a chunk
# TODO: in tests, replace region.header or region.chunk_headers with region.metadata

if __name__ == '__main__':
    logger = logging.getLogger("nbt.tests.regiontests")
    if len(logger.handlers) == 0:
        # Logging is not yet configured. Configure it.
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
    unittest.main()
