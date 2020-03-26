import asyncio
import sys
from contextlib import contextmanager
from functools import partial

from mock import Mock


def r(base, **attrs):
    """
    helper for returning Requirement subclasses with extra attributes
    """
    base.__dict__.update(attrs)
    return base


PY_VERSION = sys.version_info[:2]

PY_36 = PY_VERSION == (3, 6)


class Type1(object): pass
class Type2(object): pass
class Type3(object): pass
class Type4(object): pass


class TheType(object):
    def __repr__(self):
        return '<TheType obj>'


@contextmanager
def no_threads():
    loop = asyncio.get_event_loop()
    original = loop.run_in_executor
    loop.run_in_executor = Mock(side_effect=Exception('threads used when they should not be'))
    try:
        yield
    finally:
        loop.run_in_executor = original

@contextmanager
def must_run_in_thread(func):
    seen = set()
    loop = asyncio.get_event_loop()
    original = loop.run_in_executor

    def recording_run_in_executor(executor, func, *args):
        if isinstance(func, partial):
            to_record = func.func
        else:
            # get the underlying method for bound methods:
            to_record = getattr(func, '__func__', func)
        seen.add(to_record)
        return original(executor, func, *args)

    loop.run_in_executor = recording_run_in_executor
    try:
        yield
    finally:
        loop.run_in_executor = original

    assert func in seen, f'{func} was not run in a thread'
