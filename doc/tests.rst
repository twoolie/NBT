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

Due to insecurity of HTTPS in urllib2, it does no longer work for Python up
to 2.7.9. In that case, the external curl program is used to download a sample
file. Note that urllib2 before 2.7.9 or 3.4.2 never checked the HTTPS (x509)
certificates. A SHA256 checksum is calculated to check the validity of the
downloaded files.


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
