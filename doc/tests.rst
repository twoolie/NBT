.. _tests:

Unit tests
==========

The NBT library comes with a number of unit tests, although they have been
added later and do not cover all possible methods and options available.
These teste are automatically executed by the `Travis continuous integration
service <https://travis-ci.org/>`_.

Requirements
------------

The unit tests are written with help of unittest2. This package is available
in the standard library (as unittest) starting with Python 2.7.
Python 2.6 includes an older version of unittest, and unittest2 need to be
manually installed::

    pip install unittest2

``downloadsample`` script
-------------------------

.. automodule:: downloadsample
    :members:
    :undoc-members:
    :show-inheritance:

``nbttests`` unit test
----------------------

Unit tests for :ref:`module:nbt.nbt`

.. automodule:: nbttests
    :members:
    :undoc-members:
    :show-inheritance:

``chunktests`` unit test
------------------------

Unit tests for :ref:`module:nbt.chunk`

*No tests available (yet)*

..  commented out; no tests exist yet
    automodule:: chunktests
    :members:
    :undoc-members:
    :show-inheritance:

``regiontests`` unit test
-------------------------

Unit tests for :ref:`module:nbt.region`

..  automodule:: regiontests
    :members:
    :undoc-members:
    :show-inheritance:

``worldtests`` unit test
------------------------

Unit tests for :ref:`module:nbt.world`

*No tests available (yet)*

..  commented out; no tests exist yet
    automodule:: worldtests
    :members:
    :undoc-members:
    :show-inheritance:
