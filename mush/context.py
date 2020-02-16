from typing import Optional, Any, Union, Type

from .declarations import nothing, extract_requires
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

    def add(self,
            resource: Any,
            provides: Optional[Union[Type, str]] = None):
        """
        Add a resource to the context.

        Optionally specify what the resource provides.
        """
        if provides is None:
            provides = type(resource)
        if provides is NONE_TYPE:
            raise ValueError('Cannot add None to context')
        if provides in self._store:
            raise ContextError('Context already contains %r' % (
                    provides
                    ))
        self._store[provides] = resource

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

        for requirement in requires:
            o = self.get(requirement)
            if o is nothing:
                pass
            elif requirement.target is None:
                args.append(o)
            else:
                kw[requirement.target] = o

        return obj(*args, **kw)

    def get(self, requirement):
        # extract requirement?
        o = self._store.get(requirement.base, missing)
        if isinstance(o, Factory):
            o = o(self)

        for op in requirement.ops:
            o = op(o)
            if o is nothing:
                break

        if o is missing:
            raise ContextError('No %s in context' % repr(requirement.spec))

        return o
