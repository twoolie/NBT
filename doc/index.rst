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
==================

Modules
-------

.. toctree::
    :maxdepth: 1

    nbt
    world
    region
    chunk

Constants
---------

.. autodata:: nbt.VERSION

Functions
---------

.. autofunction:: nbt._get_version


Auxiliary Documentation
=======================

.. toctree::
    examples
    specification

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
