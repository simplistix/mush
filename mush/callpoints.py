from .declarations import (
    requires_nothing, returns as returns_declaration, returns_nothing
)
from .extraction import extract_requires, extract_returns
from .requirements import Call, name_or_repr


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
            key = returns.args[0]
            requirement = Call(obj, requires)
            if key in runner.lazy:
                raise TypeError(
                    f'{name_or_repr(key)} has more than one lazy definition:\n'
                    f'{runner.lazy[key]}\n'
                    f'{requirement}'
                )
            runner.lazy[key] = requirement
            obj = do_nothing
            requires = requires_nothing
            returns = returns_nothing
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
