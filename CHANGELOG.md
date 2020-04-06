Changelog
=========

0.5.0
-----

* Add trailing slash to package directory links at the root index.  Useful, for example,
  with nginx proxy configurations, such as using the `ngx_aws_auth` module, where
  directory paths can't be detected by the server.

0.4.0
-----

* Fixed importing of configparser with Python 3 (PR #1)

* Fixed a bug related to uploading tar.gz files to s3 (PR #2)

* Added a CLI option to display the installed version

* Fixed project name in upload path as per PEP-503 (Issue #3)

* The tool is now fully compatible with PEP-440 which ensures that the
  artifacts for the given version are correctly identified and
  uploaded. This changed requires `setuptools` to be added as a
  project dependency.


0.3.2
-----

* Fixed local file system backend

* Added travis config file


0.3.1
-----

* Fixed package URL in setup.py to point to the github repo. This
  ensures the Homepage link on PyPI points to the github repo.

* Minor fixes in the README


0.3.0
-----

First public version released
