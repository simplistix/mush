from .context import Context
from .declarations import nothing, extract_requires, extract_returns
from .resolvers import Lazy


class CallPoint(object):

    next = None
    previous = None

    def __init__(self, obj, requires=None, returns=None, lazy=None):
        requires = extract_requires(obj, requires)
        returns = extract_returns(obj, returns)
        lazy = lazy or getattr(obj, '__mush__', {}).get('lazy')
        if lazy:
            obj = Lazy(obj, requires, returns)
            requires = requires(Context)
            returns = nothing
        self.obj = obj
        self.requires = requires
        self.returns = returns
        self.labels = set()
        self.added_using = set()

    def __call__(self, context):
        return context.extract(self.obj, self.requires, self.returns)

    def __repr__(self):
        txt = '%r %r %r' % (self.obj, self.requires, self.returns)
        if self.labels:
            txt += (' <-- ' + ', '.join(sorted(self.labels)))
        return txt
