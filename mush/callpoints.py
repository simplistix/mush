from .declarations import result_type, nothing, extract_declarations
from .factory import Factory


class CallPoint(object):

    next = None
    previous = None
    requires = nothing
    returns = result_type

    def __init__(self, obj, requires=None, returns=None, lazy=None):
        requires, returns = extract_declarations(obj, requires, returns)
        lazy = lazy or getattr(obj, '__mush_lazy__', False)
        requires = requires or nothing
        returns = returns or result_type
        if lazy:
            obj = Factory(obj, requires, returns)
            requires = returns = nothing
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
