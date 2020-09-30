from types import FunctionType
from typing import Callable, Optional, Type

from .markers import missing
from .typing import Resource, Identifier


def type_repr(type_):
    if isinstance(type_, type):
        return type_.__qualname__
    elif isinstance(type_, FunctionType):
        return type_.__name__
    else:
        return repr(type_)


class ResourceKey(tuple):

    def __new__(cls, type_: Type = None, identifier: Identifier = None):
        return tuple.__new__(cls, (type_, identifier))

    @property
    def type(self) -> Type:
        return self[0]

    @property
    def identifier(self) -> Identifier:
        return self[1]

    def __str__(self):
        type_ = self.type
        if type_ is None:
            return repr(self.identifier)
        type_repr_ = type_repr(type_)
        if self.identifier is None:
            return type_repr_
        return f'{type_repr_}, {self.identifier!r}'

    def __repr__(self):
        return f'ResourceKey({self})'


class ResourceValue:

    provider: Optional[Callable] = None
    provides_subclasses: bool = False

    def __init__(self, obj: Resource):
        self.obj = obj

    def __repr__(self):
        return repr(self.obj)


class Provider(ResourceValue):

    def __init__(self, obj: Callable, *, cache: bool = True, provides_subclasses: bool = False):
        super().__init__(missing)
        self.provider = obj
        self.cache = cache
        self.provides_subclasses = provides_subclasses

    def __repr__(self):
        obj_repr = '' if self.obj is missing else f'cached={self.obj!r}, '
        return (f'Provider({self.provider}, {obj_repr}'
                f'cache={self.cache}, '
                f'provides_subclasses={self.provides_subclasses})')
