**Region Module**

*exception* region.RegionHeaderError
	Exception raised if there exists an Error in the header of the region file for a given chunk
	
*exception* region.ChunkHeaderError
	Exception raised if there exists an error in the header of a chunk
	
*exception* region.ChunkDataError
	Exception raised if there exists an error in the data of a chunk, included the bytes of length and byte version
	
*class* region.RegionFile(*[filename, fileobj]]*)
	A convenience class for extracting NBT files from the Minecraft Beta Region Format.  Pass either a filename or file object opened with 'rb' to utilize an existing Minecraft Region File.
	
	RegionFile.init_header()
		Setups up the header of a new region file
		
	RegionFile.parse_header()
		Pares the header of this RegionFile
	
	RegionFile.parse_chunk_headers()
		Parses the headers of all Chunks within this RegionFile
	
	RegionFile.locate_free_space()
		Currently not implemented
	
	RegionFile.get_chunks()
		Return coordinates and length of all chunks.
		Warning: despite the name, this function does not actually return the chunk, but merely it's metadata.  Use get_chunk(x,z) to get the NBTFile, and then Chunk() to get the actual chunk.	
			
	RegionFile.get_chunk_coords()
		Return coordinates and length of all Chunk in this RegionFile
	
	RegionFile.iter_chunks()
		Return an iterater over all chunks present in the region.
		Warning: this function returns a NBTFile() object, use Chunk(nbtfile) to get a Chunk instance.
		
	RegionFile.get_timestamp(*x, z*)
		Gets the timestamp of the chunk at *x, z*.  Currently does not return anythime.
	
	RegionFile.chunk_count()
		Returns a count of how many chunks have been created in this region file.
	
	RegionFile.get_nbt(*x, z*)
		Returns the NBT file of the chunk at *x, z*
		
	RegionFile.get_chunk(*x, z*)
		Returns the NBT file of the chunk at *x, z*
	
	RegionFile.write_chunk(*x, z, nbt_file*)
		Writes the given chunk to the given position in this region file.  A smart chunk writer that uses extents to trade off between fragmentation and cpu time.  
		
	RegionFile.unlink_chunk(*x, z*)
		Removes a chunk from the header of the region file (write zeros in the offset of the chunk).  Using only this method leaves the chunk data intact, fragmenting the region file (unconfirmed).  This is an start to a better function remove_chunk