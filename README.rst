pypiprivate
===========

``pypiprivate`` is a command line tool for hosting a private
PyPI_-like package index or in other words, a `manual python
repository
<https://packaging.python.org/guides/hosting-your-own-index/>`_ backed
by a file based storage.

It's implemented in a way that the storage backends are pluggable. At
present, only `AWS S3`_ and local file system are supported but more
implementations can be added in future.

The backend can be protected behind a HTTP reverse proxy (eg. Nginx_)
to allow secure private access to the packages.


How it works?
-------------

Update: We have published a blog post that explains the usage,
approach and rationale in detail - `Private Python Package Index with
Zero Hassle`_.

At present ``pypiprivate`` comes with only one command to publish a
package (more utilities for package search and discoverability are
coming soon).

A publish operation involves,

1. Copying all the available package artifacts for a specific version
   under the ``./dist`` directory to the storage backend

2. Creating the index on the same storage backend

The file structure created on the backend conforms to the "Simple
Repository API" specification defined in `PEP 503`_.

The files can now be served securely by a webserver eg. by setting up
a Nginx reverse proxy.

It's important to note that although the name of the project is
``pypiprivate``, **it's upto you to ensure that the access to both,
the storage and the index is really private**. If you are using S3 and
Nginx, for example, then

* package authors/owners will need read-write S3 creds to publish
  packages
* nginx will authenticate with S3 using read-only S3 creds and protect
  the files via HTTP Basic authentication
* package users will need HTTP Auth creds to install the packages
  using pip


Installation
------------

``pypi-private`` can be installed using pip_ as follows,

.. code-block:: bash

    $ pip install pypiprivate

After installation, a script ``pypi-private`` which will be available
at ``PATH``.

You may choose to install it in a virtualenv_, but it's recommended to
install it globally for all users (using ``sudo``) so that it's less
confusing to build and publish projects that need to use their own
virtualenvs.


Configuration
-------------

``pypiprivate`` requires it's own config file, the default location
for which is ``~/.pypi-private.cfg``. This repo contains the example
config file ``example.pypi-private.cfg``, which can be simply copied
to the home directory and renamed to ``.pypi-private.cfg``.

For ``aws-s3`` type of storage backend, two environment variables
``PP_S3_ACCESS_KEY`` and ``PP_S3_SECRET_KEY`` are required to be set
besides the config. The advantage of excluding s3 credentials in
config file are that (1) they are not stored in plain text and, (2)
it's easier to switch between read-only/read-write keys


Usage
-----

First create the builds,

.. code-block:: bash

    $ python setup.py sdist bdist_wheel

Then to publish the built artifacts run,

.. code-block:: bash

    $ pypi-private -v publish <pkg-name> <pkg-version>


For other options, run

.. code-block:: bash

    $ pypi-private -h


Fetching packages published using pypiprivate
---------------------------------------------

Run pip with the ``--extra-index-url`` option,

.. code-block:: bash

    $ pip install mypackage --extra-index-url=https://<user>:<password>@my.private.pypi.com/simple

Or, add the ``extra-index-url`` to pip config file at
``~/.pip/pip.conf`` as follows ::

    [install]
    extra-index-url = https://<user>:<password>@my.private.pypi.com/simple

And then simply run,

.. code-block:: bash

    $ pip install mypackage


License
-------

MIT (See `LICENSE <./LICENSE.txt>`_)


.. _PyPI: https://pypi.org/
.. _AWS S3: https://aws.amazon.com/s3/
.. _Nginx: http://nginx.org/
.. _pip: https://pypi.org/project/pip/
.. _virtualenv: https://virtualenv.pypa.io/
.. _PEP 503: https://www.python.org/dev/peps/pep-0503/
.. _Private Python Package Index with Zero Hassle: https://medium.com/helpshift-engineering/private-python-package-index-with-zero-hassle-6164e3831208
