from inspect import signature
from typing import Optional, Callable, Union, Any, Dict

from .extraction import extract_requires
from .markers import missing, Marker
from .requirements import Requirement
from .resources import ResourceKey, ResourceValue, Provider
from .typing import Resource, Identifier, Type_

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

    def add_by_keys(self, resource: ResourceValue, keys: Iterable[ResourceKey]):
        for key in keys:
            if key in self._store:
                raise ResourceError(f'Context already contains {key}')
            self._store[key] = resource

    def add(self,
            obj: Union[Provider, Resource],
            provides: Optional[Type_] = missing,
            identifier: Identifier = None):
        """
        Add a resource to the context.

        Optionally specify what the resource provides.

        ``provides`` can be explicitly specified as ``None`` to only register against the identifier
        """
        keys = set()
        if isinstance(obj, Provider):
            resource = obj
            if provides is missing:
                keys.update(extract_returns(resource.provider))

        else:
            resource = ResourceValue(obj)
            if provides is missing:
                provides = type(obj)

        if provides is not missing:
            keys.add(ResourceKey(provides, identifier))
        if not (identifier is None or provides is None):
            keys.add(ResourceKey(None, identifier))

        if not keys:
            raise ResourceError(
                f'Could not determine what is provided by {resource}'
            )

        self.add_by_keys(resource, keys)

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

    def _process(self, obj, result, returns):
        if returns is None:
            # returns = self._returns_cache.get(obj)
            # if returns is None:
            returns = extract_returns(obj)
                # self._returns_cache[obj] = returns

        if returns:
            self.add_by_keys(ResourceValue(result), returns)

    def extract(self, obj: Callable):#, requires: RequiresType = None, returns: ReturnsType = None):
        result = self.call(obj)
        self._process(obj, result, returns=None)
        return result

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

    def _resolve(self, obj, specials=None):
        if specials is None:
            specials: Dict[type, Any] = {Context: self}

        requires = extract_requires(obj)

        args = []
        kw = {}

        for parameter in requires:
            requirement = parameter.requirement

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
                o = parameter.default

            if o is not requirement.default:
                for op in requirement.ops:
                    o = op(o)
                    if o is missing:
                        o = requirement.default
                        break

            if o is missing:
                raise ResourceError(f'{requirement!r} could not be satisfied')

            if parameter.target is None:
                args.append(o)
            else:
                kw[parameter.target] = o

        return obj(*args, **kw)

    def call(self, obj: Callable):
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
