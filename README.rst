Mush
====

|CircleCI|_ |Docs|_

.. |CircleCI| image:: https://circleci.com/gh/Simplistix/mush/tree/master.svg?style=shield
.. _CircleCI: https://circleci.com/gh/Simplistix/mush/tree/master

.. |Docs| image:: https://readthedocs.org/projects/mush/badge/?version=latest
.. _Docs: http://mush.readthedocs.org/en/latest/

Mush is a light weight dependency injection framework aimed at
enabling the easy testing and re-use of chunks of code that make up
scripts.

This is done by combining several callables into a re-usable
runner. Those callables may produce or require resource objects which
mush passes between them based on the type of the object. The
callables are called in the order they are added to the
runner, while labels may be used to insert callables at specific points 
in the runner.
