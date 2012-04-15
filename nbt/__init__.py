__all__ = ["nbt", "world", "region", "chunk"]
from . import *

VERSION = (1, 3)

def _get_version():
	"""Return the NBT version as string."""
	return ".".join([str(v) for v in VERSION])
