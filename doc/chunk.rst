**Chunk Module**
	
**Chunk Objects**
	
*class* chunk.Chunk(*nbt*)
Return a new instance of a Chunk class, representing one Minecraft chunk
of data (16x16x128 blocks).  *nbt* is an NBT object
	
	Chunk.get_coords()
		Returns the coordinates of the chunk

*class* chunk.BlockArray(*blocksBytes=None, dataBytes=None*)
Convenience class for dealing with a Block/data byte array

	BlockArray.get_all_blocks()
		Returns a list of all block entries
	BlockArray.get_all_data()
		Returns all data entries
	BlockArray.get_all_blocks_and_data()
		Returns all block entries and data entries as a zipped list
	BlockArray.get_blocks_struct()
		Returns a dictionary of all blocks, keyed by (x, y, z) position
	BlockArray.get_blocks_byte_array(*[buffer]*)
		Returns the block list packed as a byte array.  If *buffer* is *True*, returns an in memory bytes buffer, otherwise returns an
		instance of *array.array*.
	BlockArray.get_data_byte_array(*[buffer]*)
		Returns the data list packed as a byte array.  If *buffer* is *True*, returns an in memory bytes buffer, otherwise returns an
		instance of *array.array*.
	BlockArray.generate_heightmap(*[buffer, [as_array]]*)
		Generates the heightmap of the chunk.  If *buffer* is *True*, the map is returned as an in memory byte buffer.  If *as_array* is *True*, returns the heightmap an instante of *array.array*.
	BlockArray.set_blocks(*[list, [dict, [fill_air]]]*)
		Sets the block list to be either a list, a dictionary keyed by
		(x, y, z).  If *fill_air* is *True*, coordinates not explicitly
		in the dictionary will be set to air
	BlockArray.set_block(*x,y,z, id, [data]*)
		Sets a single block at (x,y,z) to be the given id.  Optionally,
		can set metadata value to the given value.
	BlockArray.get_block(*x,y,z, [coord]*)
		Gets the block id of the block at (x,y,z).  If *coord* si supplied,
		then *coord* must be a 3-tuple of the form (x, y, z)
	BlockArray.get_data(*x,y,z, [coord]*)
		Gets the block data of the block at (x,y,z).  If *coord* si supplied, then *coord* must be a 3-tuple of the form (x, y, z)
	BlockArray.get_block_and_data(*x,y,z, [coord]*)
		Returns the tuple of (id, data) at x, y, z or at the *coord* provided.
	
	