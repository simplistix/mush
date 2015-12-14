from collections import deque

from .declarations import how, nothing
from .markers import missing

NONE_TYPE = None.__class__


class ContextError(Exception):
    """
    Errors likely caused by incorrect building of a runner.
    """
    def __init__(self, text, point=None, context=None):
        self.text = text
        self.point = point
        self.context = context

    def __str__(self):
        rows = []
        if self.point:
            point = self.point.previous
            while point:
                rows.append(repr(point))
                point = point.previous
            if rows:
                rows.append('Already called:')
                rows.append('')
                rows.append('')
                rows.reverse()
                rows.append('')

            rows.append('While calling: '+repr(self.point))
        if self.context is not None:
            rows.append('with '+repr(self.context)+':')
            rows.append('')

        rows.append(self.text)

        if self.point:
            point = self.point.next
            if point:
                rows.append('')
                rows.append('Still to call:')
            while point:
                rows.append(repr(point))
                point = point.next

        return '\n'.join(rows)

    __repr__ = __str__


def type_key(type_tuple):
    type, _ = type_tuple
    if isinstance(type, str):
        return type
    return type.__name__


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
            raise ContextError('Context already contains %r' % (
                    type
                    ))
        self[type] = it

    def __repr__(self):
        bits = []
        for type, value in sorted(self.items(), key=type_key):
            bits.append('\n    %r: %r' % (type, value))
        if bits:
            bits.append('\n')
        return '<Context: {%s}>' % ''.join(bits)

    def call(self, obj, requires, returns):

        args = []
        kw = {}

        for name, required in requires:

            type = required
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
                raise ContextError('No %s in context' % repr(required))
            elif name is None:
                args.append(o)
            else:
                kw[name] = o

        result = obj(*args, **kw)

        for type, obj in returns.process(result):
            self.add(obj, type)

        return result
