pypiprivate
===========

``pypiprivate`` is a bunch of command line utilities for hosting a
private pypi-like package index or in other words, a `manual python
repository
<https://packaging.python.org/guides/hosting-your-own-index/>`_. At
present it provides only one command line util to publish a package to
a private repo but more utilities for package search and
discoverability are coming soon.

It's implemented to support pluggable storage backends and the ones
currently supported are S3 and Local file system.

Note: Although the name of the project is ``pypiprivate``, it's upto
you to ensure that the access to the storage is really private, both -
the http endpoint and the underlying storage.


Installation
------------

This project has been published to our private repo (using
itself!). So to install it, you'll need to specify it as a
extra-index-url.

.. code-block:: bash

    $ sudo pip install pypiprivate --extra-index-url=<get-this-from-ops>

This will install a script ``pypi-private`` available at PATH.

You may choose to install it in a virtualenv, but it's recommended to
install it globally for all users (sudo required) so that it's less
confusing to build and publish projects that need to use their own
virtualenvs.


Configuration
-------------

``pypiprivate`` requires it's own config file, the default location
for which is ``~/.pypi-private.cfg``. This repo also contains the
example config file ``example.pypi-private.cfg``, which can be copied
the home directory and modified.

For `aws-s3` type of storage backend, two environment variables
``PP_S3_ACCESS_KEY`` and ``PP_S3_SECRET_KEY`` are required to be set
besides the config. The advantage of excluding s3 credentials in
config file are that (1) they are not stored in plain text and, (2)
it's easier to switch between read-only/read-write keys.


Usage
-----

First create the builds,

.. code-block:: bash

    $ python setup.py bdist_wheel

Then to publish the built artifacts run,

.. code-block:: bash

    $ pypi-private -v publish <pkg-name> <pkg-version>


For other options, run

.. code-block:: bash

    $ pypi-private -h
