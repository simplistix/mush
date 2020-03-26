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
def nonblocking(obj):
    """
    A decorator to mark a method as not requiring running
    in a thread, even though it's not async.
    """
    # Not using set_mush / get_mush to try and keep this as
    # quick as possible
    obj.__nonblocking__ = True
    return obj
