#!/usr/bin/env python
import sys,os,unittest
import tempfile, shutil
from io import BytesIO
import logging
import random
import time
import zlib

# Search parent directory first, to make sure we test the local nbt module, 
# not an installed nbt module.
parentdir = os.path.realpath(os.path.join(os.path.dirname(__file__),os.pardir))
if parentdir not in sys.path:
	sys.path.insert(1, parentdir) # insert ../ just after ./

from nbt.region import RegionFile, RegionFileFormatError, NoRegionHeader, \
	RegionHeaderError, ChunkHeaderError, ChunkDataError, InconceivedChunk
from nbt.nbt import NBTFile, TAG_Compound, TAG_Byte_Array, TAG_Long, TAG_Int, TAG_String

REGIONTESTFILE = os.path.join(os.path.dirname(__file__), 'regiontest.mca')


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
		b = b.getbuffer()
		assert len(b) == bytesize
		c = zlib.compress(b, 1)
		# check if the compressed size is sufficient.
		resultsize = len(c)
		logger.debug("try %d: uncompressed %d bytes -> compressed %d bytes" % (tries, bytesize, resultsize))
		if minsize <= resultsize <= maxsize:
			break
		# size is not good enough. Try again, with new targetsize.
		bytesize = int(round(bytesize * targetsize / resultsize))
		tries += 1
		if tries > 20:
			sys.stderr.write("Failed to generate NBT file of %d bytes after %d tries. Result is %d bytes.\n" % (targetsize, tries, resultsize))
			break
	return level

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
	sector 026: empty
	
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

	def test00MethodFileSize(self):
		"""
		Test of the get_size() method.
		The regionfile has 27 sectors.
		"""
		self.assertEqual(self.region.get_size(), 27*4096)

	def test01MethodChunkCount(self):
		"""
		Test of the chunk_count() method.
		The regionfile has 21 chunks, including 3-out of file chunks.
		"""
		self.assertEqual(self.region.chunk_count(), 21)

	def test02MethodGetChunkCoords(self):
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

	def test03MethodIterChunks(self):
		"""
		Test of iter_chunks() method.
		"""
		chunks = []
		for chunk in self.region.iter_chunks():
			self.assertIsInstance(chunk, TAG_Compound)
			chunks.append(chunk)
		self.assertEqual(len(chunks), 13)

	def test04SyntaxIterChunks(self):
		"""
		Test of iter(RegionFile) syntax.
		"""
		chunks = []
		for chunk in self.region:
			self.assertIsInstance(chunk, TAG_Compound)
			chunks.append(chunk)
		self.assertEqual(len(chunks), 13)
	
	def test05ParameterHeaders(self):
		"""
		read headers of chunk 9,0: 
		sector 6, 1 sector length, timestamp 1334530101, status STATUS_CHUNK_OK.
		read chunk headers of chunk 9,0: 
		lenght (incl. compression byte): 3969 bytes, zlip (2) compression, status STATUS_CHUNK_OK.
		"""
		self.assertEqual(self.region.header[9,0], (6, 1, 1334530101, RegionFile.STATUS_CHUNK_OK))
		self.assertEqual(self.region.chunk_headers[9,0], (3969, 2, RegionFile.STATUS_CHUNK_OK))
	
	def test06ParameterHeadersUndefinedChunk(self):
		"""
		read headers & chunk_headers of chunk 2,2
		"""
		self.assertEqual(self.region.header[2,2], (0, 0, 0, RegionFile.STATUS_CHUNK_NOT_CREATED))
		self.assertEqual(self.region.chunk_headers[2,2], (None, None, RegionFile.STATUS_CHUNK_NOT_CREATED))
	
	def test10ReadChunkZlibCompression(self):
		"""
		chunk 9,0: regular Zlib compression. Should be read OK.
		"""
		nbt = self.region.get_nbt(9, 0)
		self.assertIsInstance(nbt, TAG_Compound)
		# get_chunk is currently an alias of get_nbt
		chunk = self.region.get_chunk(9, 0)
		self.assertIsInstance(chunk, TAG_Compound)

	def test11ReadChunkGzipCompression(self):
		"""
		chunk 10,0: deprecated GZip compression. Should be read OK.
		"""
		nbt = self.region.get_nbt(10, 0)
		self.assertIsInstance(nbt, TAG_Compound)

	def test12ReadChunkUncompressed(self):
		"""
		chunk 2,0: no compression. Should be read OK.
		"""
		nbt = self.region.get_nbt(2, 0)
		self.assertIsInstance(nbt, TAG_Compound)

	def test13ReadUnknownEncoding(self):
		"""
		chunk 11,0 has unknown encoding (3). Reading should raise a ChunkDataError.
		"""
		self.assertRaises(ChunkDataError, self.region.get_nbt, 11, 0)

	def test14ReadMalformedEncoding(self):
		"""
		chunk 3,0 has malformed content. Reading should raise a ChunkDataError.
		This should not raise a MalformedFileError.
		"""
		self.assertRaises(ChunkDataError, self.region.get_nbt, 3, 0)

	# TODO: raise nbt.region.ChunkDataError instead of nbt.nbt.MalformedFileError, or make them the same.
	def test15ReadMalformedNBT(self):
		"""
		read chunk 5,1: valid compression, but not a valid NBT file. Reading should raise a ChunkDataError.
		"""
		self.assertRaises(ChunkDataError, self.region.get_nbt, 5, 1)

	def test16ReadChunkNonExistent(self):
		"""
		read chunk 2,2: does not exist. Reading should raise a InconceivedChunk.
		"""
		self.assertRaises(InconceivedChunk, self.region.get_nbt, 2, 2)

	def test17ReadableChunks(self):
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

	def test20ReadInHeader(self):
		"""
		read chunk 14,0: supposedly located in the header. 
		Reading should raise a RegionHeaderError.
		"""
		self.assertRaises(RegionHeaderError, self.region.get_nbt, 14, 0)
		# TODO:
		self.assertEqual(self.region.header[14,0], (1, 1, 1376433960, RegionFile.STATUS_CHUNK_IN_HEADER))
		self.assertEqual(self.region.chunk_headers[14,0], (None, None, RegionFile.STATUS_CHUNK_IN_HEADER))

	def test21ReadOutOfFile(self):
		"""
		read chunk 15,0: error (out of file)
		"""
		self.assertRaises(RegionHeaderError, self.region.get_nbt, 15, 0)
		self.assertEqual(self.region.header[15,0], (30, 1, 1376433961, RegionFile.STATUS_CHUNK_OUT_OF_FILE))
		self.assertEqual(self.region.chunk_headers[15,0], (None, None, RegionFile.STATUS_CHUNK_OUT_OF_FILE))

	def test22ReadZeroLengthHeader(self):
		"""
		read chunk 13,0: error (zero-length)
		"""
		self.assertRaises(RegionHeaderError, self.region.get_nbt, 13, 0)
		self.assertEqual(self.region.header[13,0], (21, 0, 1376433958, RegionFile.STATUS_CHUNK_ZERO_LENGTH))
		self.assertEqual(self.region.chunk_headers[13,0], (None, None, RegionFile.STATUS_CHUNK_ZERO_LENGTH))

	def test23ReadInvalidLengthChunk(self):
		"""
		zero-byte lengths in chunk. (4,1)
		read chunk 4,1: error (invalid)
		"""
		self.assertRaises(ChunkHeaderError, self.region.get_nbt, 4, 1)

	def test24ReadZeroLengthChunk(self):
		"""
		read chunk 8,1: error (zero-length chunk)
		"""
		self.assertRaises(ChunkHeaderError, self.region.get_nbt, 8, 1)

	def test25ReadChunkSizeExceedsSectorSize(self):
		"""
		read chunk 3,1: can be read, despite that the chunk content is longer than the allocated sectors.
		In general, reading should either succeeds, or raises a ChunkDataError.
		The status should be STATUS_CHUNK_MISMATCHED_LENGTHS.
		"""
		self.assertEqual(self.region.chunk_headers[3,1][2], RegionFile.STATUS_CHUNK_MISMATCHED_LENGTHS)
		# reading should succeed, despite the overlap (next chunk is free)
		nbt = self.region.get_nbt(3, 1)

	def test26ReadChunkOverlapping(self):
		"""
		chunk 4,0 and chunk 12,0 overlap: status should be STATUS_CHUNK_OVERLAPPING
		"""
		self.assertEqual(self.region.chunk_headers[4,0][2], RegionFile.STATUS_CHUNK_OVERLAPPING)
		self.assertEqual(self.region.chunk_headers[12,0][2], RegionFile.STATUS_CHUNK_OVERLAPPING)

	def test30GetTimestampOK(self):
		"""
		get_timestamp
		read chunk 9,0: OK
		"""
		self.assertEqual(self.region.get_timestamp(9,0), 1334530101)

	def test31GetTimestampBadChunk(self):
		"""
		read chunk 15,0: OK
		Data is out-out-of-file, but timestamp is still there.
		"""
		self.assertEqual(self.region.get_timestamp(15,0), 1376433961)

	def test32GetTimestampNoChunk(self):
		"""
		read chunk 17,0: OK
		no data, but a timestamp
		"""
		self.assertEqual(self.region.get_timestamp(17,0), 1334530101)

	def test33GetTimestampMissing(self):
		"""
		read chunk 7,1: OK
		data, but no timestamp
		"""
		self.assertEqual(self.region.get_timestamp(7,1), 0)

	def test40WriteNewChunk(self):
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

	def test41WriteAndReadNewChunk(self):
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

	def test42WriteExistingChunk(self):
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

	def test43DeleteChunk(self):
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

	# TODO: bug in free sector calculation for overlapping chunks
	@unittest.expectedFailure
	def test44UseEmptyChunks(self):
		"""
		write 1 sector chunk 1,2 (should go to 004)
		write 1 sector chunk 2,2 (should go to 010)
		write 1 sector chunk 3,2 (should go to 011)
		write 1 sector chunk 4,2 (should go to 026)
		verify file size remains 027*4096
		"""
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
		locations.sort()
		self.assertEqual(locations, [4, 10, 11, 26])

	def test50WriteNewChunk2sector(self):
		"""
		write 2 sector chunk 1,2 (should go to 010-011)
		"""
		nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
		self.region.write_chunk(1, 2, nbt)
		header = self.region.header[1, 2]
		self.assertEqual(header[1], 2, "Chunk length must be 2 sectors")
		self.assertEqual(header[0], 10, "Chunk should be placed in sector 10")
		self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)

	def test51WriteNewChunk4096byte(self):
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

	def test52WriteNewChunk4097byte(self):
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

	# TODO: file increasement should be supported
	@unittest.expectedFailure
	def test53WriteNewChunkIncreaseFile(self):
		"""
		write 3 sector chunk 2,2 (should go to 026-028) (increase file size)
		verify file size is 29*4096
		"""
		nbt = generate_compressed_level(minsize = 9000, maxsize = 11000)
		self.region.write_chunk(1, 2, nbt)
		header = self.region.header[1, 2]
		self.assertEqual(header[1], 3, "Chunk length must be 3 sectors")
		self.assertEqual(header[0], 26, "Chunk should be placed in sector 26")
		self.assertEqual(self.region.get_size(), 29*4096)
		self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)

	def test54WriteExistingChunkDecreaseSector(self):
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

	# TODO: increased chunk should remain in place, if possible
	@unittest.expectedFailure
	def test60WriteExistingChunkIncreaseSectorSameLocation(self):
		"""
		write 2 sector chunk 1,2 (should go to 010-011)
		write 2 sector chunk 7,0 (should go to 003-004) (increase chunk size)
		"""
		nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
		self.region.write_chunk(1, 2, nbt)
		header = self.region.header[1, 2]
		self.assertEqual(header[1], 2)
		self.assertEqual(header[0], 10)
		self.region.write_chunk(7, 0, nbt)
		header = self.region.header[7, 0]
		self.assertEqual(header[1], 2, "Chunk length must be 2 sectors")
		self.assertEqual(header[0], 3, "Chunk should remain in sector 3")
		self.assertEqual(header[3], RegionFile.STATUS_CHUNK_OK)
		# self.assertEqual(self.region.get_size(), 27*4096)

	def test61WriteExistingChunkIncreaseSectorNewLocation(self):
		"""
		write 2 sector chunk 8,0 (should go to 010-011) (increase chunk size, move to different location)
		verify chunk_count remains 18
		should free sector 005
		write 2 sector chunk 2,2 (should go to 004-005)
		verify that file size is not increased <= 027*4096
		verify chunk_count is 19
		"""
		chunk_count = self.region.chunk_count()
		nbt = generate_compressed_level(minsize = 5000, maxsize = 7000)
		self.region.write_chunk(8, 0, nbt)
		header = self.region.header[8, 0]
		self.assertEqual(header[1], 2) # length
		self.assertEqual(header[0], 10) # location
		self.assertEqual(self.region.chunk_count(), chunk_count)
		# Section 005 should be free now.
		self.region.write_chunk(2, 2, nbt)
		header = self.region.header[2, 2]
		self.assertEqual(header[1], 2) # length
		self.assertEqual(header[0], 4) # location
		self.assertEqual(self.region.chunk_count(), chunk_count + 1)

	def test62WriteNewChunkFreedSectors(self):
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

	@unittest.expectedFailure
	def test70WriteOutOfFileChunk(self):
		"""
		write 1 sector chunk 13,0 (should go to 004)
		Should not go to sector 30 (out-of-file location)
		"""
		nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
		self.region.write_chunk(13, 0, nbt)
		header = self.region.header[13, 0]
		self.assertEqual(header[1], 1) # length
		self.assertLessEqual(header[0], 26, "Previously out-of-file chunk should be written in-file")

	def test71WriteZeroLengthSectorChunk(self):
		"""
		write 1 sector chunk 13,0 (should go to 004)
		Verify sector 19 remains untouched.
		"""
		nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
		self.region.write_chunk(13, 0, nbt)
		header = self.region.header[13, 0]
		self.assertEqual(header[1], 1) # length
		self.assertNotEqual(header[0], 19, "Previously 0-length chunk should not overwrite existing chunk")

	# TODO: Chunk should not be written to same location when it overlaps
	@unittest.expectedFailure
	def test72WriteOverlappingChunkLong(self):
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
		self.assertNotEqual(header[0], 14, "Chunk should not be written to same location when it overlaps")
		self.assertEqual(header[0], 10, "Chunk should not be written to same location when it overlaps")
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

	# TODO: Chunk should not be written to same location when it overlaps
	@unittest.expectedFailure
	def test73WriteOverlappingChunkSmall(self):
		"""
		write 1 sector chunk 12,0 (should go to 004) ("free" 015 for use by 4,0)
		verify location is NOT 015
		verify sectors 15 and 16 are not marked as "free", but remain in use by 4,0
		"""
		nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
		self.region.write_chunk(12, 0, nbt)
		header = self.region.header[12, 0]
		self.assertEqual(header[1], 1) # length
		self.assertNotEqual(header[0], 15, "Chunk should not be written to same location when it overlaps")
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

	# TODO: Chunk should not be written to same location when it overlaps
	@unittest.expectedFailure
	def test74WriteOverlappingChunkSameLocation(self):
		"""
		write 1 sector chunk 12,0 (should go to 004) ("free" 012 for use by 4,0)
		write 3 sector chunk 4,0 (should stay in 014-016)
		verify file size remains <= 027*4096
		"""
		nbt = generate_compressed_level(minsize = 100, maxsize = 4000)
		self.region.write_chunk(12, 0, nbt)
		header = self.region.header[12, 0]
		self.assertEqual(header[1], 1) # length
		self.assertNotEqual(header[0], 15, "Chunk should not be written to same location when it overlaps")
		nbt = generate_compressed_level(minsize = 9000, maxsize = 11000)
		self.region.write_chunk(4, 0, nbt)
		header = self.region.header[4, 0]
		self.assertEqual(header[1], 3) # length
		self.assertNotEqual(header[0], 14, "No longer overlapping chunks should be written to same location when when possible")

	# TODO: bug in free sector calculation for overlapping chunks (precondition fails)
	@unittest.expectedFailure
	def test80FileTruncateSimple(self):
		"""
		write 1 sector chunk 1,2 (should go to 004)
		write 1 sector chunk 2,2 (should go to 010)
		write 1 sector chunk 3,2 (should go to 011)
		write 1 sector chunk 4,2 (should go to 026)
		delete chunk 1,2
		delete chunk 2,2
		delete chunk 3,2
		delete chunk 4,2 (free 026: truncate file size)
		verify file size: 26*4096 bytes
		"""
		self.assertEqual(self.region.get_size(), 27*4096)
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
		self.assertEqual(locations, [4, 10, 11, 26])
		self.region.unlink_chunk(1, 2)
		self.region.unlink_chunk(2, 2)
		self.region.unlink_chunk(3, 2)
		self.region.unlink_chunk(4, 2)
		self.assertEqual(self.region.get_size(), 26*4096, "Removing the last chunk in the file should reduce the file size")

	# TODO: File should be truncated when last sector(s) are freed
	@unittest.expectedFailure
	def test81FileTruncateFreeTail(self):
		"""
		delete chunk 3,1 (free 025: truncate file size)
		verify file size: 25*4096 bytes
		"""
		self.region.unlink_chunk(3, 1)
		self.assertEqual(self.region.get_size(), 25*4096, "File should be truncated when last sector(s) are freed")

	# TODO: File should be truncated when last sector(s) are freed
	@unittest.expectedFailure
	def test82FileTruncateMergeFree(self):
		"""
		delete chunk 8,1 (free 024)
		delete chunk 3,1 (free 025: truncate file size, including 024)
		verify file size: 24*4096 bytes
		"""
		self.region.unlink_chunk(8, 1)
		self.region.unlink_chunk(3, 1)
		self.assertEqual(self.region.get_size(), 24*4096, "File should be truncated as far as possible when last sector(s) are freed")

	# TODO: enable test again
	@unittest.skip('Test takes too much time')
	# TODO: Check for maximum sector size.
	@unittest.expectedFailure
	def test90WriteChunkTooLarge(self):
		"""
		Chunks of size >= 256 sectors are not supported by the file format
		attempt to write a chunk 256 sectors in size
		should raise Exception
		"""
		maxsize = 256 * 4096
		nbt = generate_compressed_level(minsize = maxsize + 100, maxsize = maxsize + 4000)
		self.assertRaises(ChunkDataError, self.region.write_chunk, 2, 2, nbt)

	# TODO: Unused bytes in sector should be zeroed after writing
	@unittest.expectedFailure
	def test91WriteZeroPadding(self):
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
		self.region.file.seek(sectorlocation + chunklength)
		unused = self.region.file.read(unusedlength)
		zeroes = unused.count(b'\x00')
		self.assertEqual(zeroes, unusedlength, "All unused bytes should be zeroed after writing a chunk")
	
	# TODO: Sector should be zeroed after unlinking
	@unittest.expectedFailure
	def test92DeleteZeroPadding(self):
		"""
		unlink chunk 7,1
		Check if all bytes in sector 022 are zeroed.
		"""
		header = self.region.header[7, 1]
		sectorlocation = header[0]
		self.region.unlink_chunk(7, 1)
		self.region.file.seek(sectorlocation)
		unused = self.region.file.read(4096)
		zeroes = unused.count(b'\x00')
		self.assertEqual(zeroes, 4096, "All bytes should be zeroed after deleting a chunk")
	
	def test93DeleteOverlappingNoZeroPadding(self):
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
		self.assertNotEqual(zeroes, 4096, "Bytes should be zeroed after deleting an overlapping chunk")
	
	def test94DeleteZeroPaddingMismatchLength(self):
		"""
		unlink chunk 3,1. (which has a length mismatch)
		Check if bytes in sector 025 are all zeroed.
		Check if first byte in sector 026 is not zeroed.
		"""
		raise unittest.SkipTest("Test can't use this testfile")
	

	# 
	# 
	# def testReadBig(self):
	# 	mynbt = NBTFile(self.filename)
	# 	self.assertTrue(mynbt.filename != None)
	# 	self.assertEqual(len(mynbt.tags), 11)
	# 
	# def testWriteBig(self):
	# 	mynbt = NBTFile(self.filename)
	# 	output = BytesIO()
	# 	mynbt.write_file(buffer=output)
	# 	self.assertEqual(GzipFile(REGIONTESTFILE).read(), output.getvalue())
	# 
	# def testWriteback(self):
	# 	mynbt = NBTFile(self.filename)
	# 	mynbt.write_file()




class EmptyFileTest(unittest.TestCase):
	"""Test for 0-byte file support.
	These files should be treated as a valid region file without any stored chunk."""
#TODO: add the following tests:
# * read 0-byte region file
# * ... and then write a 1-sector chunk to it. Make sure headers are created, and file size is 3*4096 bytes.
	
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

	def test01ReadFile(self):
		self.stream = BytesIO(b"")
		self.stream.seek(0)
		region = RegionFile(fileobj=self.stream)
		self.assertEqual(region.chunk_count(), 0)
	
	# TODO: Known failure; silence unittest for the time being
	@unittest.expectedFailure
	def test02WriteFile(self):
		chunk = self.generate_level()
		self.stream = BytesIO(b"")
		self.stream.seek(0)
		region = RegionFile(fileobj=self.stream)
		region.write_chunk(0, 0, chunk)
		self.assertEqual(self.region.get_size(), 3*4096)
		self.assertEqual(self.region.chunk_count(), 1)

# TODO: test suite to test the different __init__ parameters of RegionFile
# (filename or fileobj), write to it, delete RegionFile object, and test if:
# - file is properly written to
# - file is closed (for filename)
# - file is not closed (for fileobj)
# Also test if an exception is raised if RegionFile is called incorrectly (e.g. both filename and fileobj are specified, or none)

# TODO: test what happens with a corrupt region file, of 5000 bytes in size. Read a chunk, write a chunk
# TODO: test what happens if a file is trucated, but the chunk is still readable. This should return the chunk.
#       also test writing; does the file get padded?

if __name__ == '__main__':
	logger = logging.getLogger("nbt.tests.regiontests")
	if len(logger.handlers) == 0:
		# Logging is not yet configured. Configure it.
		logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
	if sys.version_info[0:2] >= (2,7):
		unittest.main(verbosity=2, catchbreak=True)
	else:
		unittest.main()
