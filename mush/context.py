from collections import deque

from .declarations import how, nothing
from mush import missing

NONE_TYPE = None.__class__


class Context(dict):
    "Stores resources for a particular run."

    def add(self, it, type):
        """
        Add a resource to the context.

        Optionally specify the type to use for the object rather than
        the type of the object itself.
        """

        if type is NONE_TYPE:
            raise ValueError('Cannot add None to context')
        if type in self:
            raise ValueError('Context already contains %r' % (
                    type
                    ))
        self[type] = it

    def __repr__(self):
        return '<Context: %s>' % super(Context, self).__repr__()

    def call(self, obj, requires, returns):

        args = []
        kw = {}

        for name, type in requires:

            ops = deque()
            while isinstance(type, how):
                ops.appendleft(type.process)
                type = type.type

            o = self.get(type, missing)

            for op in ops:
                o = op(o)
                if o is nothing:
                    break

            if o is nothing:
                pass
            elif o is missing:
                raise KeyError('No %r in context' % type)
            elif name is None:
                args.append(o)
            else:
                kw[name] = o

        result = obj(*args, **kw)

        for type, obj in returns.process(result):
            self.add(obj, type)

        return result
