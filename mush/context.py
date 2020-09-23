from inspect import signature
from typing import Optional, Callable, Hashable, Type, Union, Mapping, Any, Dict

from .requirements import Requirement
from .declarations import RequiresType
from .extraction import extract_requires
from .markers import missing, Marker
from .resources import ResourceKey, Resource, Provider
from .typing import ResourceValue

NONE_TYPE = type(None)
unspecified = Marker('unspecified')


class ResourceError(Exception):
    """
    An exception raised when there is a problem with a resource.
    """


class Context:
    "Stores resources for a particular run."

    # _parent: 'Context' = None
    # point: CallPoint = None

    def __init__(self):
        self._store = {}
        # self._requires_cache = {}
        # self._returns_cache = {}

    def add(self,
            obj: Union[Provider, ResourceValue],
            provides: Optional[Type] = missing,
            identifier: Hashable = None):
        """
        Add a resource to the context.

        Optionally specify what the resource provides.

        ``provides`` can be explicitly specified as ``None`` to only register against the identifier
        """
        if isinstance(obj, Provider):
            resource = obj
            if provides is missing:
                sig = signature(obj.provider)
                annotation = sig.return_annotation
                if annotation is sig.empty:
                    if identifier is None:
                        raise ResourceError(
                            f'Could not determine what is provided by {obj.provider}'
                        )
                else:
                    provides = annotation

        else:
            resource = Resource(obj)
            if provides is missing:
                provides = type(obj)

        to_add = []
        if provides is not missing:
            to_add.append(ResourceKey(provides, identifier))
        if not (identifier is None or provides is None):
            to_add.append(ResourceKey(None, identifier))
        for key in to_add:
            if key in self._store:
                raise ResourceError(f'Context already contains {key}')
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
            bits.append(f'\n    {key}: {value!r}')
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

    def _find_resource(self, key):
        if not isinstance(key[0], type):
            return self._store.get(key)
        type_, identifier = key
        exact = True
        for type__ in type_.__mro__:
            resource = self._store.get((type__, identifier))
            if resource is not None and (exact or resource.provides_subclasses):
                return resource
            exact = False

    def _resolve(self, obj, specials = None):
        if specials is None:
            specials: Dict[type, Any] = {Context: self}

        requires = extract_requires(obj)

        args = []
        kw = {}

        for requirement in requires:

            o = missing

            for key in requirement.keys:

                resource = self._find_resource(key)

                if resource is None:
                    o = specials.get(key[0], missing)
                else:
                    if resource.obj is missing:
                        specials_ = specials.copy()
                        specials_[Requirement] = requirement
                        o = self._resolve(resource.provider, specials_)
                        if resource.cache:
                            resource.obj = o
                    else:
                        o = resource.obj

                if o is not missing:
                    break

            if o is missing:
                o = requirement.default

            # if o is not requirement.default:
            #     for op in requirement.ops:
            #         o = op(o)
            #         if o is missing:
            #             o = requirement.default
            #             break

            if o is missing:
                raise ResourceError(f'{requirement!r} could not be satisfied')

            # if requirement.target is None:
            args.append(o)

        return obj(*args, **kw)

    def call(self, obj: Callable, requires: RequiresType = None):
        return self._resolve(obj)

    #
    # def nest(self, requirement_modifier: RequirementModifier = None):
    #     if requirement_modifier is None:
    #         requirement_modifier = self.requirement_modifier
    #     nested = self.__class__(requirement_modifier)
    #     nested._parent = self
    #     nested._requires_cache = self._requires_cache
    #     nested._returns_cache = self._returns_cache
    #     return nested
