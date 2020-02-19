from typing import Optional

from .declarations import (
    nothing, extract_requires, RequiresType,
    ResourceKey, ResourceValue, Resolver
)
from .markers import missing
from .resolvers import ValueResolver

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
            resource: Optional[ResourceValue] = None,
            provides: Optional[ResourceKey] = None,
            resolver: Optional[Resolver] = None):
        """
        Add a resource to the context.

        Optionally specify what the resource provides.
        """
        if resolver is not None and (provides is None or resource is not None):
            if resource is not None:
                raise TypeError('resource cannot be supplied when using a resolver')
            raise TypeError('Both provides and resolver must be supplied')
        if provides is None:
            provides = type(resource)
        if provides is NONE_TYPE:
            raise ValueError('Cannot add None to context')
        if provides in self._store:
            raise ContextError(f'Context already contains {provides!r}')
        if resolver is None:
            resolver = ValueResolver(resource)
        self._store[provides] = resolver

    def remove(self, key: ResourceKey, *, strict: bool = True):
        """
        Remove the specified resource key from the context.

        If ``strict``, then a :class:`ContextError` will be raised if the
        specified resource is not present in the context.
        """
        if strict and key not in self._store:
            raise ContextError(f'Context does not contain {key!r}')
        self._store.pop(key, None)

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
        if requires.__class__ is not RequiresType:
            requires = extract_requires(obj, requires)

        args = []
        kw = {}

        for target, requirement in requires:
            o = self.get(requirement.key, requirement.default)

            for op in requirement.ops:
                o = op(o)
                if o is nothing:
                    break

            if o is missing:
                raise ContextError('No %s in context' % repr(requirement.spec))

            if o is nothing:
                pass
            elif target is None:
                args.append(o)
            else:
                kw[target] = o

        return obj(*args, **kw)

    def get(self, key: ResourceKey, default=None):
        resolver = self._store.get(key, None)
        if resolver is None:
            if key is Context:
                return self
            return default
        return resolver(self, default)
