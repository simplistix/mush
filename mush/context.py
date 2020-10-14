from collections import namedtuple
from typing import Optional, Callable, Union, Any, Dict, Iterable

from .callpoints import CallPoint
from .extraction import extract_requires, extract_returns
from .markers import missing, Marker
from .requirements import Requirement, Annotation
from .resources import ResourceKey, ResourceValue, Provider
from .typing import Resource, Identifier, Type_, Requires, Returns, DefaultRequirement

NONE_TYPE = type(None)
unspecified = Marker('unspecified')


class ResourceError(Exception):
    """
    An exception raised when there is a problem with a resource.
    """


Call = namedtuple('Call', ('obj', 'args', 'kw', 'send'))


class Context:
    "Stores resources for a particular run."

    _parent: 'Context' = None
    point: CallPoint = None

    def __init__(self, default_requirement: DefaultRequirement = Annotation):
        self._store = {}
        self._default_requirement = default_requirement

    def add_by_keys(self, resource: ResourceValue, keys: Iterable[ResourceKey]):
        keys_ = keys
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

    def __repr__(self):
        bits = []
        for key, value in sorted(self._store.items(), key=lambda o: repr(o)):
            bits.append(f'\n    {key}: {value!r}')
        if bits:
            bits.append('\n')
        return f"<Context: {{{''.join(bits)}}}>"

    def extract(self, obj: Callable, requires: Requires = None, returns: Returns = None):
        result = self.call(obj, requires)
        returns = extract_returns(obj, returns)
        if returns:
            self.add_by_keys(ResourceValue(result), returns)
        return result

    def _find_resource(self, key):
        exact = True
        if not isinstance(key[0], type):
            return self._store.get(key), exact
        type_, identifier = key
        for type__ in type_.__mro__:
            resource = self._store.get((type__, identifier))
            if resource is not None and (exact or resource.provides_subclasses):
                return resource, exact
            exact = False
        return None, exact

    def _specials(self) -> Dict[type, Any]:
        return {Context: self}

    def _resolve(self, obj, requires=None, specials=None):
        if specials is None:
            specials = self._specials()

        requires = extract_requires(obj, requires, self._default_requirement)

        args = []
        kw = {}

        for parameter in requires:
            requirement = parameter.requirement

            o = missing
            first_key = None

            for key in requirement.keys:
                if first_key is None:
                    first_key = key

                context = self

                while True:
                    resource, exact = context._find_resource(key)

                    if resource is None:
                        o = specials.get(key[0], missing)
                    else:
                        if resource.obj is missing:
                            specials_ = specials.copy()
                            specials_[Requirement] = requirement
                            specials_[ResourceKey] = first_key
                            o = context._resolve(resource.provider, specials=specials_)
                            provider = resource.provider
                            resolving = context._resolve(provider, specials=specials_)
                            for call in resolving:
                                o = yield Call(call.obj, call.args, call.kw, send=True)
                                yield
                                if call.send:
                                    resolving.send(o)
                            if resource.cache:
                                if exact and context is self:
                                    resource.obj = o
                                else:
                                    self.add_by_keys(ResourceValue(o), (key,))
                        else:
                            o = resource.obj

                    if o is not missing:
                        break

                    context = context._parent
                    if context is None:
                        break

                if o is not missing:
                    break

            if o is missing:
                o = parameter.default

            if o is not requirement.default:
                o = requirement.process(o)

            if o is missing:
                raise ResourceError(f'{requirement!r} could not be satisfied')

            if parameter.target is None:
                args.append(o)
            else:
                kw[parameter.target] = o

        yield Call(obj, args, kw, send=False)

    def call(self, obj: Callable, requires: Requires = None):
        resolving = self._resolve(obj, requires)
        for call in resolving:
            result = call.obj(*call.args, **call.kw)
            if call.send:
                resolving.send(result)
        return result

    def nest(self):
        nested = self.__class__(self._default_requirement)
        nested._parent = self
        return nested
