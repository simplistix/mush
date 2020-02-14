from collections import deque

from .declarations import how, nothing, extract_requires
from .factory import Factory
from .markers import missing

NONE_TYPE = type(None)


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


class Context:
    "Stores resources for a particular run."

    def __init__(self):
        self._store = {}

    def add(self, it, type):
        """
        Add a resource to the context.

        Optionally specify the type to use for the object rather than
        the type of the object itself.
        """

        if type is NONE_TYPE:
            raise ValueError('Cannot add None to context')
        if type in self._store:
            raise ContextError('Context already contains %r' % (
                    type
                    ))
        self._store[type] = it

    def __repr__(self):
        bits = []
        for type, value in sorted(self._store.items(), key=type_key):
            bits.append('\n    %r: %r' % (type, value))
        if bits:
            bits.append('\n')
        return '<Context: {%s}>' % ''.join(bits)

    def extract(self, obj, requires, returns):
        result = self.call(obj, requires)
        for type, obj in returns.process(result):
            self.add(obj, type)
        return result

    def call(self, obj, requires=None):
        requires = extract_requires(obj, requires)

        if isinstance(obj, Factory):
            self.add(obj, obj.returns.args[0])
            return

        args = []
        kw = {}

        for name, requirement in requires:
            o = self.get(requirement)
            if o is nothing:
                pass
            elif name is None:
                args.append(o)
            else:
                kw[name] = o

        return obj(*args, **kw)

    def get(self, requirement):
        spec = requirement
        ops = deque()

        while isinstance(spec, how):
            ops.appendleft(spec.process)
            spec = spec.type

        o = self._store.get(spec, missing)
        if isinstance(o, Factory):
            o = o(self)

        for op in ops:
            o = op(o)
            if o is nothing:
                break

        if o is missing:
            raise ContextError('No %s in context' % repr(requirement))

        return o
