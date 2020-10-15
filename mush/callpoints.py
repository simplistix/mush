from typing import TYPE_CHECKING, Callable

from .extraction import extract_requires, extract_returns
from .typing import Requires, Returns

if TYPE_CHECKING:
    from . import Context


class CallPoint(object):

    next = None
    previous = None

    def __init__(self, obj: Callable, requires: Requires = None, returns: Returns = None):
        self.obj = obj
        self.requires = requires
        self.returns = returns
        self.labels = set()
        self.added_using = set()

    def __call__(self, context: 'Context'):
        return context.extract(self.obj, self.requires, self.returns)

    def __repr__(self):
        requires = extract_requires(self.obj, self.requires)
        returns = extract_returns(self.obj, self.returns)
        name = getattr(self.obj, '__qualname__', repr(self.obj))
        txt = f'{name} {requires!r} {returns!r}'
        if self.labels:
            txt += (' <-- ' + ', '.join(sorted(self.labels)))
        return txt
