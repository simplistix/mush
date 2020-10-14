from typing import Any, List, Sequence, Optional, Union, Type

from .markers import missing
from .resources import ResourceKey, type_repr, is_type
from .typing import Identifier, Type_


class Op:

    def __init__(self, name):
        self.name = name

    def __call__(self, o):  # pragma: no cover
        raise NotImplementedError()


class AttrOp(Op):

    def __call__(self, o):
        try:
            return getattr(o, self.name)
        except AttributeError:
            return missing

    def __repr__(self):
        return f'.{self.name}'


class ItemOp(Op):

    def __call__(self, o):
        try:
            return o[self.name]
        except KeyError:
            return missing

    def __repr__(self):
        return f'[{self.name!r}]'


class Requirement:
    """
    The requirement for an individual parameter of a callable.
    """

    def __init__(self, keys: Sequence[ResourceKey], default: Optional[Any] = missing):
        #: Note that the first key returned should be the "most specific"
        self.keys: Sequence[ResourceKey] = keys
        self.default = default
        self.ops: List['Op'] = []

    def _keys_repr(self):
        return ', '.join(repr(key) for key in self.keys)

    def __repr__(self):
        default = '' if self.default is missing else f', default={self.default!r}'
        ops = ''.join(repr(o) for o in self.ops)
        return f"{type(self).__name__}({self._keys_repr()}{default}){ops}"

    def attr(self, name):
        """
        If you need to get an attribute called either ``attr`` or ``item``
        then you will need to call this method instead of using the
        generating behaviour.
        """
        self.ops.append(AttrOp(name))
        return self

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return self.attr(name)

    def __getitem__(self, name):
        self.ops.append(ItemOp(name))
        return self

    def complete(self, name: str, type_: Type_, default: Any):
        return self

    def process(self, obj):
        for op in self.ops:
            obj = op(obj)
            if obj is missing:
                obj = self.default
                break
        return obj


class Annotation(Requirement):

    def __init__(self, name: str, type_: Type_ = None, default: Any = missing):
        if type_ is None:
            keys = [ResourceKey(None, name)]
        else:
            keys = [
                ResourceKey(type_, name),
                ResourceKey(type_, None),
                ResourceKey(None, name),
            ]
        super().__init__(keys, default)

    def __repr__(self):
        type_, name = self.keys[0]
        r = name
        if type_ is not None:
            r += f': {type_repr(type_)}'
        if self.default is not missing:
            r += f' = {self.default!r}'
        return r


class Value(Requirement):
    """
    Declaration indicating that the specified resource key is required.

    Values are generative, so they can be used to indicate attributes or
    items from a resource are required.

    A default may be specified, which will be used if the specified
    resource is not available.

    A type may also be explicitly specified, but you probably shouldn't
    ever use this.
    """

    def __init__(self,
                 key: Union[Type_, Identifier] = None,
                 identifier: Identifier = None,
                 default: Any = missing):
        if identifier is None:
            if key is None:
                raise TypeError('type or identifier must be supplied')
            resource_key = ResourceKey.guess(key)
        else:
            resource_key = ResourceKey(key, identifier)
        super().__init__([resource_key], default)

    def _keys_repr(self):
        return str(self.keys[0])


class AnyOf(Requirement):
    """
    A requirement that is resolved by any of the specified keys.

    A key may either be a :class:`type` or an :class:`Identifier`
    """

    def __init__(self, *keys: Union[Type_, Identifier], default: Any = missing):
        if not keys:
            raise TypeError('at least one key must be specified')
        resource_keys = []
        for key in keys:
            type_ = identifier = None
            if is_type(key):
                type_ = key
            else:
                identifier = key
            resource_keys.append(ResourceKey(type_, identifier))
        super().__init__(resource_keys, default)

    def _keys_repr(self):
        return ', '.join(str(key) for key in self.keys)


class Like(Requirement):
    """
    A requirements that is resolved by the specified class or
    any of its base classes.
    """

    def __init__(self, type_: type, default: Any = missing):
        keys = []
        for type__ in type_.__mro__:
            if type__ is object:
                break
            keys.append(ResourceKey(type__, None))
        super().__init__(keys, default)

    def _keys_repr(self):
        return str(self.keys[0])
