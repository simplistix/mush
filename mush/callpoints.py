from .declarations import (
    nothing, returns as returns_declaration

)
from .extraction import extract_requires, extract_returns


def do_nothing():
    pass


class CallPoint(object):

    next = None
    previous = None

    def __init__(self, runner, obj, requires=None, returns=None, lazy=False):
        requires = extract_requires(obj, requires, runner.modify_requirement)
        returns = extract_returns(obj, returns)
        if lazy:
            if not (type(returns) is returns_declaration and len(returns.args) == 1):
                raise TypeError('a single return type must be explicitly specified')
            runner.lazy[returns.args[0]] = obj, requires
            obj = do_nothing
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
