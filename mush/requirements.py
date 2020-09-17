from typing import Any, List, TYPE_CHECKING, Hashable, Sequence

from .markers import missing, nonblocking
from .resources import ResourceKey

if TYPE_CHECKING:
    from .context import Context


def name_or_repr(obj):
    return getattr(obj, '__name__', None) or repr(obj)


class Op:

    def __init__(self, name):
        self.name = name


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

    def __init__(self, default: Any, *keys: Sequence[ResourceKey]):
        self.keys = keys
        self.default = default
        self.ops: List['Op'] = []
    #     self.target: Optional[str] = target

    def _keys_repr(self):
        return ', '.join(repr(key) for key in self.keys)

    def __repr__(self):
        default = '' if self.default is missing else f', default={self.default!r}'
        ops = ''.join(repr(o) for o in self.ops)
        return f"{type(self).__name__}({self._keys_repr()}{default}){ops}"
    #
    # def attr(self, name):
    #     """
    #     If you need to get an attribute called either ``attr`` or ``item``
    #     then you will need to call this method instead of using the
    #     generating behaviour.
    #     """
    #     self.ops.append(AttrOp(name))
    #     return self
    #
    # def __getattr__(self, name):
    #     if name.startswith('__'):
    #         raise AttributeError(name)
    #     return self.attr(name)
    #
    # def __getitem__(self, name):
    #     self.ops.append(ItemOp(name))
    #     return self


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

    def __init__(self, type_: type = None, identifier: Hashable = None, default: Any = missing):
        super().__init__(
            default,
            ResourceKey(type_, identifier),
            ResourceKey(None, identifier),
            ResourceKey(type_, None),
        )

    def _keys_repr(self):
        return str(self.keys[0])

#
#
# class AnyOf(Requirement):
#     """
#     A requirement that is resolved by any of the specified keys.
#     """
#
#     def __init__(self, *keys, default=missing):
#         super().__init__(keys, default=default)
#
#     @nonblocking
#     def resolve(self, context: 'Context'):
#         for key in self.key:
#             value = context.get(key, missing)
#             if value is not missing:
#                 return value
#         return self.default
#
#
# class Like(Requirement):
#     """
#     A requirements that is resolved by the specified class or
#     any of its base classes.
#     """
#
#     @nonblocking
#     def resolve(self, context: 'Context'):
#         for key in self.key.__mro__:
#             if key is object:
#                 break
#             value = context.get(key, missing)
#             if value is not missing:
#                 return value
#         return self.default
#
#
# class Lazy(Requirement):
#
#     def __init__(self, original, provider):
#         super().__init__(original.key)
#         self.original = original
#         self.provider = provider
#         self.ops = original.ops
#
#     def resolve(self, context):
#         resource = context.get(self.key, missing)
#         if resource is missing:
#             context.extract(self.provider.obj, self.provider.requires, self.provider.returns)
#         return self.original.resolve(context)
