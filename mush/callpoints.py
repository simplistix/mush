from .declarations import (
    result_type, nothing, requires as RequiresType,
    returns as Returns, returns_result_type as ReturnsType
)


class CallPoint(object):

    next = None
    previous = None
    requires = nothing
    returns = result_type

    def __init__(self, obj, requires=None, returns=None):
        self.obj = obj

        if requires is None:
            self.requires = getattr(obj, '__mush_requires__', nothing)
        else:
            if isinstance(requires, (list, tuple)):
                requires = RequiresType(*requires)
            elif not isinstance(requires, RequiresType):
                requires = RequiresType(requires)
            self.requires = requires

        if returns is None:
            self.returns = getattr(obj, '__mush_returns__', result_type)
        else:
            if isinstance(returns, (list, tuple)):
                returns = Returns(*returns)
            elif not isinstance(returns, ReturnsType):
                returns = Returns(returns)
            self.returns = returns

        self.labels = set()
        self.added_using = set()

    def __call__(self, context):
        return context.call(self.obj, self.requires, self.returns)

    def __repr__(self):
        txt = '%r %r %r' % (self.obj, self.requires, self.returns)
        if self.labels:
            txt += (' <-- ' + ', '.join(sorted(self.labels)))
        return txt
