NBT's documentation
===================

NBT is a Named Binary Tag parser based upon the specification by Markus Persson.

From the spec:
  "NBT (Named Binary Tag) is a tag based binary format designed to carry large
   amounts of binary data with smaller amounts of additional data.
   An NBT file consists of a single GZIPped Named Tag of type TAG_Compound."

This project also contains helper classes for dealing with Regions and Chunks in
Minecraft, the main use case for the NBT format.

Contents:

:mod:`nbt` Package
------------------

.. automodule:: nbt
    :members:
    :private-members:
    :special-members:
    :undoc-members:
    :show-inheritance:

.. toctree::
    :maxdepth: 1

    nbt
    world
    region
    chunk

Auxiliary Documentation
-----------------------

.. toctree::
    examples
    specification


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

