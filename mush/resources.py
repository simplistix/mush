from typing import Callable, Optional

from .markers import missing
from .typing import ResourceValue


class ResourceKey(tuple):

    def __new__(cls, type_, identifier):
        return tuple.__new__(cls, (type_, identifier))

    @property
    def type(self):
        return self[0]

    @property
    def identifier(self):
        return self[1]

    def __str__(self):
        if self.type is None:
            return repr(self.identifier)
        if hasattr(self.type, '__supertype__'):
            type_repr = f'NewType({self.type.__name__}, {self.type.__supertype__})'
        else:
            type_repr = repr(self.type)
        if self.identifier is None:
            return type_repr
        return f'{type_repr}, {self.identifier!r}'


class Resource:

    provider: Optional[Callable] = None
    provides_subclasses: bool = False

    def __init__(self, obj: ResourceValue):
        self.obj = obj

    def __repr__(self):
        return repr(self.obj)


class Provider(Resource):

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
