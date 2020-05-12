from copy import copy
from typing import Any, Optional, List, TYPE_CHECKING

from .typing import ResourceKey
from .markers import missing, nonblocking

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

    def __init__(self,
                 key: ResourceKey,
                 name: str = None,
                 type_: type = None,
                 default: Any = missing,
                 target: str = None):
        #: The resource key needed for this parameter.
        self.key: Optional[ResourceKey] = key
        #: The name of this parameter in the callable's signature.
        self.name: Optional[str] = name
        #: The type required for this parameter.
        self.type: Optional[type] = type_
        #: The default for this parameter, should the required resource be unavailable.
        self.default: Optional[Any] = default
        #: Any operations to be performed on the resource after it
        #: has been obtained.
        self.ops: List['Op'] = []
        self.target: Optional[str] = target

    @classmethod
    def make(cls, **attrs):
        """
        Make a :class:`Requirement` instance with all attributes provided.

        .. note::

          This method allows instances to be created with missing or invalid attributes.
          While this is necessary for use cases such as testing :class:`Requirement`
          instantiation or otherwise setting attributes that are not accessible from
          a custom requirement's :meth:`__init__`, it should be used with care.

        :param attrs:
        :return:
        """
        obj = Requirement(attrs.pop('key'))
        obj.__class__ = cls
        obj.__dict__.update(attrs)
        return obj

    @classmethod
    def make_from(cls, source: 'Requirement', **attrs):
        """
        Make a new instance of this requirement class, using attributes
        from a source requirement overlaid with any additional
        ``attrs`` that have been supplied.
        """
        attrs_ = source.__dict__.copy()
        attrs_.update(attrs)
        obj = cls.make(**attrs_)
        obj.ops = list(source.ops)
        obj.default = copy(source.default)
        return obj

    def resolve(self, context: 'Context'):
        raise NotImplementedError()

    def __repr__(self):
        key = name_or_repr(self.key)
        default = '' if self.default is missing else f', default={self.default!r}'
        ops = ''.join(repr(o) for o in self.ops)
        return f"{type(self).__name__}({key}{default}){ops}"

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

    def __init__(self, key: ResourceKey = None, *, type_: type = None, default: Any = missing):
        if isinstance(key, type):
            if type_ is not None:
                raise TypeError('type_ cannot be specified if key is a type')
            type_ = key
        super().__init__(key, type_=type_, default=default)

    @nonblocking
    def resolve(self, context: 'Context'):
        return context.get(self.key, self.default)


class AnyOf(Requirement):
    """
    A requirement that is resolved by any of the specified keys.
    """

    def __init__(self, *keys, default=missing):
        super().__init__(keys, default=default)

    @nonblocking
    def resolve(self, context: 'Context'):
        for key in self.key:
            value = context.get(key, missing)
            if value is not missing:
                return value
        return self.default


class Like(Requirement):
    """
    A requirements that is resolved by the specified class or
    any of its base classes.
    """

    @nonblocking
    def resolve(self, context: 'Context'):
        for key in self.key.__mro__:
            if key is object:
                break
            value = context.get(key, missing)
            if value is not missing:
                return value
        return self.default


class Lazy(Requirement):

    def __init__(self, original, provider):
        super().__init__(original.key)
        self.original = original
        self.provider = provider
        self.ops = original.ops

    def resolve(self, context):
        resource = context.get(self.key, missing)
        if resource is missing:
            context.extract(self.provider.obj, self.provider.requires, self.provider.returns)
        return self.original.resolve(context)
