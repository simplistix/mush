from typing import Optional, Callable, Hashable, Type

from .callpoints import CallPoint
from .declarations import RequiresType, ReturnsType
from .extraction import extract_requires, extract_returns, default_requirement_type
from .markers import missing, Marker
from .requirements import Requirement
from .typing import ResourceValue, RequirementModifier

NONE_TYPE = type(None)
unspecified = Marker('unspecified')


class ResourceError(Exception):
    """
    An exception raised when there is a problem with a `ResourceKey`.
    """

    def __init__(self, message: str, type_: Type = None, identifier: Hashable = None):
        super().__init__(message)
        #: The type for the problematic resource.
        self.type: Type = type_
        #: The identifier for the problematic resource.
        self.identifier: Hashable = identifier
        # #: The requirement that caused this exception.
        # self.requirement: Requirement = requirement


class ResourceKey(tuple):

    @property
    def type(self):
        return self[0]

    @property
    def identifier(self):
        return self[1]

    def __repr__(self):
        if self.type is None:
            return repr(self.identifier)
        elif self.identifier is None:
            return repr(self.type)
        return f'{self.type!r}, {self.identifier!r}'


class Context:
    "Stores resources for a particular run."

    # _parent: 'Context' = None
    # point: CallPoint = None

    def __init__(self):
        self._store = {}
        self._seen_types = set()
        self._seen_identifiers = set()
        # self._requires_cache = {}
        # self._returns_cache = {}

    def add(self,
            resource: ResourceValue,
            provides: Optional[Type] = missing,
            identifier: Hashable = None):
        """
        Add a resource to the context.

        Optionally specify what the resource provides.
        """
        if provides is missing:
            provides = type(resource)
        to_add = [ResourceKey((provides, identifier))]
        if identifier and provides:
            to_add.append(ResourceKey((None, identifier)))
        for key in to_add:
            if key in self._store:
                raise ResourceError(f'Context already contains {key!r}', *key)
            self._store[key] = resource

    # def remove(self, key: ResourceKey, *, strict: bool = True):
    #     """
    #     Remove the specified resource key from the context.
    #
    #     If ``strict``, then a :class:`ResourceError` will be raised if the
    #     specified resource is not present in the context.
    #     """
    #     if strict and key not in self._store:
    #         raise ResourceError(f'Context does not contain {key!r}', key)
    #     self._store.pop(key, None)
    #
    def __repr__(self):
        bits = []
        for key, value in sorted(self._store.items(), key=lambda o: repr(o)):
            bits.append(f'\n    {key!r}: {value!r}')
        if bits:
            bits.append('\n')
        return f"<Context: {{{''.join(bits)}}}>"
    #
    # def _process(self, obj, result, returns):
    #     if returns is None:
    #         returns = self._returns_cache.get(obj)
    #         if returns is None:
    #             returns = extract_returns(obj, explicit=None)
    #             self._returns_cache[obj] = returns
    #
    #     for type, obj in returns.process(result):
    #         self.add(obj, type)
    #
    # def extract(self, obj: Callable, requires: RequiresType = None, returns: ReturnsType = None):
    #     result = self.call(obj, requires)
    #     self._process(obj, result, returns)
    #     return result
    #
    # def _resolve(self, obj, requires, args, kw, context):
    #
    #     if requires is None:
    #         requires = self._requires_cache.get(obj)
    #         if requires is None:
    #             requires = extract_requires(obj,
    #                                         explicit=None,
    #                                         modifier=self.requirement_modifier)
    #             self._requires_cache[obj] = requires
    #
    #     for requirement in requires:
    #         o = yield requirement
    #
    #         if o is not requirement.default:
    #             for op in requirement.ops:
    #                 o = op(o)
    #                 if o is missing:
    #                     o = requirement.default
    #                     break
    #
    #         if o is missing:
    #             key = requirement.key
    #             if isinstance(key, type) and issubclass(key, Context):
    #                 o = context
    #             else:
    #                 raise ResourceError(f'No {requirement!r} in context',
    #                                     key, requirement)
    #
    #         if requirement.target is None:
    #             args.append(o)
    #         else:
    #             kw[requirement.target] = o
    #
    #         yield

    def call(self, obj: Callable, requires: RequiresType = None):
        args = []
        kw = {}
        # resolving = self._resolve(obj, requires, args, kw, self)
        # for requirement in resolving:
        #     resolving.send(requirement.resolve(self))

        return obj(*args, **kw)
    #
    # def get(self, key: ResourceKey, default=unspecified):
    #     context = self
    #
    #     while context is not None:
    #         value = context._store.get(key, missing)
    #         if value is missing:
    #             context = context._parent
    #         else:
    #             if context is not self:
    #                 self._store[key] = value
    #             return value
    #
    #     if default is unspecified:
    #         raise ResourceError(f'No {key!r} in context', key)
    #
    #     return default
    #
    # def nest(self, requirement_modifier: RequirementModifier = None):
    #     if requirement_modifier is None:
    #         requirement_modifier = self.requirement_modifier
    #     nested = self.__class__(requirement_modifier)
    #     nested._parent = self
    #     nested._requires_cache = self._requires_cache
    #     nested._returns_cache = self._returns_cache
    #     return nested
