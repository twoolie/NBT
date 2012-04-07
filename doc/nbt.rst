**NBT Module**

*nbt*.TAG_END
	The end tag of an open TAG_COMPOUNT.

*nbt*.TAG_BYTE
	The type of a single signed byte.

*nbt*.TAG_SHORT
	The type of a single signed short.

*nbt*.TAG_INT
	The type of a single signed integer.

*nbt*.TAG_LONG
	The type of a single signed long.

*nbt*.TAG_FLOAT
	The type of a single IEEE-754 single-precision floating point number.

*nbt*.TAG_DOUBLE
	The type of a single IEEE-754 double-precision floating point number.

*nbt*.TAG_BYTE_ARRAY
		The type of a length-prefixed array of signed bytes. The prefix is a signed integer (thus 4 bytes).

*nbt*.TAG_STRING
	The type of a length-prefixed UTF-8 string. The prefix is an unsigned short (thus 2 bytes) 

*nbt*.TAG_LIST
	The type of a list of nameless tags, all of the same type. The list is prefixed with the Type ID of the items it contains (thus 1 byte), and the length of the list as a signed integer (a further 4 bytes)

*nbt*.TAG_COMPOUND
	The type of a list of named tags of varying types.  The end is signified by TAG_END

*nbt*.TAG_INT_ARRAY
	The type of a list of signed integers (Length prefixed?)

*nbt*.MalformedFileError
	Exception raised on parse error of a file.
	
*class* TAG(*[value, name]]*)
	Base class for the preceding tag types.  *value* and *name* are supplied when creating a new tag.

*class* TAG_BYTE
	Class that represents a single tag of type *TAG_BYTE*

*class* TAG_Short
	Class that represents a single tag of type *TAG_SHORT*

*class* TAG_Int
	Class that represents a single tag of type *TAG_INT*

*class* TAG_Long
	Class that represents a single tag of type *TAG_LONG*

*class* TAG_Float
	Class that represents a single tag of type *TAG_FLOAT*

*class* TAG_Double
	Class that represents a single tag of type *TAG_DOUBLE*

*class* TAG_Byte_Array
	Class that represents a single tag of type *TAG_BYTE_ARRAY*.  This class is comparable to a collections.UserList with an intrinsic name whose values must be bytes

*class* TAG_Int_Array
	Class that represents a single tag of type *TAG_INT_ARRAY*.  This class is comparable to a collections.UserList with an intrinsic name whose values must be integers

*class* TAG_String
	Class that represents a single tag of type *TAG_STRING*.  This class is comparable to a collections.UserString with an intrinsic name

*class* TAG_List
	Class that represents a single tag of type *TAG_LIST*.  This class is comparable to a collections.UserList with an intrinsic name

*class* TAG_Compound
	Class that represents a single tag of type *TAG_COMPOUND*.  This class is comparable to a collections.OrderedDict with an intrinsic name

*class* NBTFile(*[filename, buffer, fileobj]]]*)
	This class represents an NBT file object.  This class can be created with a filename, buffer or an opened file object.  Not passing any of these parameters will created an empty NBT file.  Inherites from TAG_Compound
	
	NBTFile.parse_file(*[filename, buffer, fileobj]]]*)
		If the NBTFile object was created without parameters, this method can be used to parse a file.  Raises *MalformedFileError* and *ValueError*.
	
	NBTFile.write_file(*[filename, buffer, fileobj]]]*)
		Writes this object to the given filename, buffer or file object.  Raises *ValueError*.