import sys


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
