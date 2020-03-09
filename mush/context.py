from typing import Optional, Type, Callable

from .declarations import RequiresType, ReturnsType
from .extraction import extract_requires, extract_returns, default_requirement_type
from .markers import missing
from .requirements import Requirement, Value
from .types import ResourceKey, ResourceValue, ResourceResolver, RequirementModifier

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


class ResolvableValue:
    __slots__ = ('value', 'resolver')

    def __init__(self, value, resolver=None):
        self.value = value
        self.resolver = resolver

    def __repr__(self):
        if self.resolver is None:
            return repr(self.value)
        return repr(self.resolver)


class Context:
    "Stores resources for a particular run."

    _parent = None

    def __init__(self, requirement_modifier: RequirementModifier = default_requirement_type):
        self._requirement_modifier = requirement_modifier
        self._store = {}
        self._requires_cache = {}
        self._returns_cache = {}

    def add(self,
            resource: Optional[ResourceValue] = None,
            provides: Optional[ResourceKey] = None,
            resolver: Optional[ResourceResolver] = None):
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
        self._store[provides] = ResolvableValue(resource, resolver)

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

    def _process(self, obj, result, returns):
        if returns is None:
            returns = self._returns_cache.get(obj)
            if returns is None:
                returns = extract_returns(obj, explicit=None)
                self._returns_cache[obj] = returns

        for type, obj in returns.process(result):
            self.add(obj, type)

    def extract(self, obj: Callable, requires: RequiresType = None, returns: ReturnsType = None):
        result = self.call(obj, requires)
        self._process(obj, result, returns)
        return result

    def _resolve(self, obj, requires, args, kw, context):

        if requires is None:
            requires = self._requires_cache.get(obj)
            if requires is None:
                requires = extract_requires(obj,
                                            explicit=None,
                                            modifier=self._requirement_modifier)
                self._requires_cache[obj] = requires

        for requirement in requires:
            o = yield requirement

            if o is not requirement.default:
                for op in requirement.ops:
                    o = op(o)
                    if o is missing:
                        o = requirement.default
                        break

            if o is missing:
                key = requirement.key
                if isinstance(key, type) and issubclass(key, Context):
                    o = context
                else:
                    raise ContextError('No %s in context' % requirement.value_repr())

            if requirement.target is None:
                args.append(o)
            else:
                kw[requirement.target] = o

            yield

    def call(self, obj: Callable, requires: RequiresType = None):
        args = []
        kw = {}
        resolving = self._resolve(obj, requires, args, kw, self)
        for requirement in resolving:
            resolving.send(requirement.resolve(self))
        return obj(*args, **kw)

    def _get(self, key, default):
        context = self
        resolvable = None

        while resolvable is None and context is not None:
            resolvable = context._store.get(key, None)
            if resolvable is None:
                context = context._parent
            elif context is not self:
                self._store[key] = resolvable

        if resolvable is None:
            return ResolvableValue(default)

        return resolvable

    def get(self, key: ResourceKey, default=None):
        resolvable = self._get(key, default)
        if resolvable.resolver is not None:
            return resolvable.resolver(self, default)
        return resolvable.value

    def nest(self, requirement_modifier: RequirementModifier = None):
        if requirement_modifier is None:
            requirement_modifier = self._requirement_modifier
        nested = self.__class__(requirement_modifier)
        nested._parent = self
        nested._requires_cache = self._requires_cache
        nested._returns_cache = self._returns_cache
        return nested
