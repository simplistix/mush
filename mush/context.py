from typing import Optional, Callable

from .callpoints import CallPoint
from .declarations import RequiresType, ReturnsType
from .extraction import extract_requires, extract_returns, default_requirement_type
from .markers import missing
from .requirements import Requirement
from .typing import ResourceKey, ResourceValue, RequirementModifier

NONE_TYPE = type(None)


class ResourceError(Exception):
    """
    An exception raised when there is a problem with a `ResourceKey`.
    """

    def __init__(self, message: str, key: ResourceKey, requirement: Requirement = None):
        super().__init__(message)
        #: The key for the problematic resource.
        self.key: ResourceKey = key
        #: The requirement that caused this exception.
        self.requirement: Requirement = requirement


class Context:
    "Stores resources for a particular run."

    _parent: 'Context' = None
    point: CallPoint = None

    def __init__(self, requirement_modifier: RequirementModifier = default_requirement_type):
        self._requirement_modifier = requirement_modifier
        self._store = {}
        self._requires_cache = {}
        self._returns_cache = {}

    def add(self,
            resource: Optional[ResourceValue] = None,
            provides: Optional[ResourceKey] = None):
        """
        Add a resource to the context.

        Optionally specify what the resource provides.
        """
        if provides is None:
            provides = type(resource)
        if provides is NONE_TYPE:
            raise ValueError('Cannot add None to context')
        if provides in self._store:
            raise ResourceError(f'Context already contains {provides!r}', provides)
        self._store[provides] = resource

    def remove(self, key: ResourceKey, *, strict: bool = True):
        """
        Remove the specified resource key from the context.

        If ``strict``, then a :class:`ResourceError` will be raised if the
        specified resource is not present in the context.
        """
        if strict and key not in self._store:
            raise ResourceError(f'Context does not contain {key!r}', key)
        self._store.pop(key, None)

    def __repr__(self):
        bits = []
        for type, value in sorted(self._store.items(), key=lambda o: repr(o)):
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
                    raise ResourceError(f'No {requirement!r} in context',
                                        key, requirement)

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

    def get(self, key: ResourceKey, default=None):
        context = self

        while context is not None:
            value = context._store.get(key, missing)
            if value is missing:
                context = context._parent
            else:
                if context is not self:
                    self._store[key] = value
                return value

        return default

    def nest(self, requirement_modifier: RequirementModifier = None):
        if requirement_modifier is None:
            requirement_modifier = self._requirement_modifier
        nested = self.__class__(requirement_modifier)
        nested._parent = self
        nested._requires_cache = self._requires_cache
        nested._returns_cache = self._returns_cache
        return nested
