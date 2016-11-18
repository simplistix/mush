|Travis|_ |Coveralls|_ |Docs|_

.. |Travis| image:: https://api.travis-ci.org/Simplistix/mush.svg?branch=master
.. _Travis: https://travis-ci.org/Simplistix/mush

.. |Coveralls| image:: https://coveralls.io/repos/Simplistix/mush/badge.svg?branch=master
.. _Coveralls: https://coveralls.io/r/Simplistix/mush?branch=master

.. |Docs| image:: https://readthedocs.org/projects/mush/badge/?version=latest
.. _Docs: http://mush.readthedocs.org/en/latest/

Mush
====

Mush is a light weight dependency injection framework aimed at
enabling the easy testing and re-use of chunks of code that make up
scripts.

This is done by combining several callables into a re-usable
runner. Those callables may produce or require resource objects which
mush passes between them based on the type of the object. The
callables are called in the order they are added to the
runner, while labels may be used to insert callables at specific points 
in the runner.

Licensing
=========

Copyright (c) 2013 Simplistix Ltd, 2015-2016 Chris Withers.
See docs/license.txt for details.
