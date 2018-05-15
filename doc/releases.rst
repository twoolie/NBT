.. _releases:

Releases (information for maintainers of the NBT package)
=========================================================

The aim is to make NBT easily obtainable by all users.

Creating a release
------------------

Change the following files::

    doc/changelog.rst
    CONTRIBUTORS.txt   (Add new contributors in alphabetic order)
    nbt/__init__.py    (Change VERSION constant)

Commit the changes, add a tag, and upload the changes::

    git add doc/changelog.rst CONTRIBUTORS.txt nbt/__init__.py
    git commit -m "Bump version number to x.y.z"
    git tag -a version-x.y.z HEAD
    git push --tags

Generate and upload the documentation: see :ref:`documentation`.

Create a release at GitHub
--------------------------

* Go to https://github.com/twoolie/NBT/releases
* Click the "Draft a new release" button
* Select the tag, and add a Release title (e.g. NBT-x.y) and release notes. I usually only list the most important changes, and add a link to the Changelog on the wiki for more details.

Create a release at PyPI
--------------------------

Follow the process described at https://packaging.python.org/tutorials/distributing-packages/.

Install requirements::

    pip install --upgrade pip
    pip install setuptools wheel twine

Create both a source (.tar.gz) and wheel (.whl) distribution::

    python setup.py sdist
    python setup.py bdist_wheel --universal

Upload all that was created to PyPI::

    ls dist/
    twine upload dist/*