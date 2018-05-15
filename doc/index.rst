===================
NBT's documentation
===================

NBT is a Named Binary Tag parser based upon the specification by Markus Persson.

From the :ref:`nbt-specification`:

    "NBT (Named Binary Tag) is a tag based binary format designed to carry large
    amounts of binary data with smaller amounts of additional data."

This project also contains helper classes for dealing with Regions, Chunks and 
World folders in Minecraft, the main use case for the NBT format.


:mod:`nbt` Package
==================

Modules
-------

.. toctree::
    :maxdepth: 1

    nbt
    chunk
    region
    world

Constants
---------

.. autodata:: nbt.VERSION

Functions
---------

.. autofunction:: nbt._get_version


Auxiliary Documentation
=======================

.. toctree::
    :maxdepth: 1

    examples
    specification
    changelog
    tests
    documentation
    releases


Indices and tables
==================

.. .. only:: html

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
