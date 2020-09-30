import asyncio
from enum import Enum, auto


class Marker(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Marker: %s>' % self.name


not_specified = Marker('not_specified')

#: A sentinel object to indicate that a value is missing.
missing = Marker('missing')


def set_mush(obj, key, value):
    if not hasattr(obj, '__mush__'):
        obj.__mush__ = {}
    obj.__mush__[key] = value


def get_mush(obj, key, default):
    __mush__ = getattr(obj, '__mush__', missing)
    if __mush__ is missing:
        return default
    return __mush__.get(key, default)


class AsyncType(Enum):
    blocking = auto()
    nonblocking = auto()
    async_ = auto()


def nonblocking(obj):
    """
    A decorator to mark a callable as not requiring running
    in a thread, even though it's not async.
    """
    set_mush(obj, 'async', AsyncType.nonblocking)
    return obj


def blocking(obj):
    """
    A decorator to explicitly mark a callable as requiring running
    in a thread.
    """
    if asyncio.iscoroutinefunction(obj):
        raise TypeError('cannot mark an async function as blocking')
    set_mush(obj, 'async', AsyncType.blocking)
    return obj
