.. _documentation:

Documentation (information for maintainers of the NBT package)
==============================================================

The documentation of the NBT library is available on the wiki
(https://github.com/twoolie/NBT/wiki), and is automatically generated from the
source code in combination with auxiliary files in the doc directory.

Requirements
------------

Install requirements::

    pip install sphinx
    pip install sphinxcontrib-restbuilder
    pip install pygments

Check out the wiki repository and make a symlink to it::

    git clone https://github.com/twoolie/NBT.wiki.git
    cd path_to/NBT/doc
    ln -s path_to/NBT.wiki

Generate the documentation
--------------------------

Generate the documentation::

    cd path_to/NBT/doc
    make wiki

Alternatively, execute the following command

::

    sphinx-build -b rst -d path_to/NBT/doc/build/doctrees -c path_to/NBT/doc \
            -a path_to/NBT/doc path_to/NBT/doc/NBT.wiki

Upload the documentation

Verify the documentation and upload the changes::

    cd path_to/NBT.wiki
    git status
    git add *
    git commit -m "Update documentation"
    git push

Sphinx Build System
-------------------

The following files are used by the documentation build system:

``Makefile``
    Build script. Run as "make wiki". Calls sphinx-build.
``conf.py``
    Sphinx configuration file. Defines settings specific for this build system.
``python.inv``
    Intersphinx mapping from classes in the standard library to a documentation 
    URL. This is only an excerpt from http://docs.python.org/3.2/objects.inv,
    and in version 1 of the Sphinx inventory format.

The following directories are used by the documentation build system. Both are 
ignored by git.

``build``
    Build folder where cache files and output of Sphinx is stored.
``NBT.wiki``
    Symbolic link to a checkout of the NBT.wiki git repository.

Known Bugs
----------

The genindex, modindex and search page are only generated for HTML, not for the wiki.

