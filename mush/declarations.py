from copy import copy
from enum import Enum, auto
from itertools import chain
from typing import Type, Callable, NewType, Union, Any, List, Optional

from .markers import missing

ResourceKey = NewType('ResourceKey', Union[Type, str])
ResourceValue = NewType('ResourceValue', Any)
ResourceResolver = Callable[['Context', Any], ResourceValue]
RequirementResolver = Callable[['Context'], ResourceValue]


def name_or_repr(obj):
    return getattr(obj, '__name__', None) or repr(obj)


def set_mush(obj, key, value):
    if not hasattr(obj, '__mush__'):
        obj.__mush__ = {}
    obj.__mush__[key] = value


class Requirement:
    """
    The requirement for an individual parameter of a callable.
    """

    resolve: RequirementResolver = None

    def __init__(self, key, name=None, type_=None, default=missing, target=None):
        self.key: ResourceKey = key
        self.name: str = (key if isinstance(key, str) else None) if name is None else name
        self.type: type = (key if not isinstance(key, str) else None) if type_ is None else type_
        self.target: Optional[str] = target
        self.default: Any = default
        #: Any operations to be performed on the resource after it
        #: has been obtained.
        self.ops: List['ValueOp'] = []

    def clone(self):
        """
        Create a copy of this requirement, so it can be mutated
        """
        obj = copy(self)
        obj.ops = list(self.ops)
        return obj

    def value_repr(self):
        key = name_or_repr(self.key)
        if self.ops or self.default is not missing:
            default = '' if self.default is missing else f', default={self.default!r}'
            ops = ''.join(repr(o) for o in self.ops)
            return f'Value({key}{default}){ops}'
        return key

    def __repr__(self):
        attrs = []
        for a in 'name', 'type_', 'target':
            value = getattr(self, a.rstrip('_'))
            if value is not None:
                attrs.append(f", {a}={value!r}")
        return f"{type(self).__name__}({self.value_repr()}{''.join(attrs)})"


class Value:
    """
    Declaration indicating that the specified resource key is required.

    Values are generative, so they can be used to indicate attributes or
    items from a resource are required.

    A default may be specified, which will be used if the specified
    resource is not available.

    A type may also be explicitly specified, but you probably shouldn't
    ever use this.
    """

    def __init__(self, key: ResourceKey, *, type_: type = None, default: Any = missing):
        self.requirement = Requirement(key, type_=type_, default=default)

    def attr(self, name):
        """
        If you need to get an attribute called either ``attr`` or ``item``
        then you will need to call this method instead of using the
        generating behaviour.
        """
        self.requirement.ops.append(ValueAttrOp(name))
        return self

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return self.attr(name)

    def __getitem__(self, name):
        self.requirement.ops.append(ValueItemOp(name))
        return self

    def __repr__(self):
        return self.requirement.value_repr()


class ValueOp:

    def __init__(self, name):
        self.name = name


class ValueAttrOp(ValueOp):

    def __call__(self, o):
        try:
            return getattr(o, self.name)
        except AttributeError:
            return missing

    def __repr__(self):
        return f'.{self.name}'


class ValueItemOp(ValueOp):

    def __call__(self, o):
        try:
            return o[self.name]
        except KeyError:
            return missing

    def __repr__(self):
        return f'[{self.name!r}]'


class RequiresType(list):

    def __repr__(self):
        parts = (r.value_repr() if r.target is None else f'{r.target}={r.value_repr()}'
                 for r in self)
        return f"requires({', '.join(parts)})"

    def __call__(self, obj):
        set_mush(obj, 'requires', self)
        return obj


def requires(*args, **kw):
    """
    Represents requirements for a particular callable.

    The passed in ``args`` and ``kw`` should map to the types, including
    any required :class:`~.declarations.how`, for the matching
    arguments or keyword parameters the callable requires.

    String names for resources must be used instead of types where the callable
    returning those resources is configured to return the named resource.
    """
    requires_ = RequiresType()
    valid_decoration_types(*args)
    valid_decoration_types(*kw.values())
    for target, possible in chain(
        ((None, arg) for arg in args),
        kw.items(),
    ):
        if isinstance(possible, Value):
            possible = possible.requirement
        if isinstance(possible, Requirement):
            possible = possible.clone()
            possible.target = target
            requirement = possible
        else:
            requirement = Requirement(possible, target=target)
        requires_.append(requirement)
    return requires_


class ReturnsType(object):

    def __call__(self, obj):
        set_mush(obj, 'returns', self)
        return obj

    def __repr__(self):
        return self.__class__.__name__ + '()'


class returns_result_type(ReturnsType):
    """
    Default declaration that indicates a callable's return value
    should be used as a resource based on the type of the object returned.

    ``None`` is ignored as a return value.
    """

    def process(self, obj):
        if obj is not None:
            yield obj.__class__, obj


class returns_mapping(ReturnsType):
    """
    Declaration that indicates a callable returns a mapping of type or name
    to resource.
    """

    def process(self, mapping):
        return mapping.items()


class returns_sequence(returns_result_type):
    """
    Declaration that indicates a callable's returns a sequence of values
    that should be used as a resources based on the type of the object returned.

    Any ``None`` values in the sequence are ignored.
    """

    def process(self, sequence):
        super_process = super(returns_sequence, self).process
        for obj in sequence:
            for pair in super_process(obj):
                yield pair


class returns(returns_result_type):
    """
    Declaration that specifies names for returned resources or overrides
    the type of a returned resource.

    This declaration can be used to indicate the type or name of a single
    returned resource or, if multiple arguments are passed, that the callable
    will return a sequence of values where each one should be named or have its
    type overridden.
    """

    def __init__(self, *args):
        valid_decoration_types(*args)
        self.args = args

    def process(self, obj):
        if len(self.args) == 1:
            yield self.args[0], obj
        else:
            for t, o in zip(self.args, obj):
                yield t, o

    def __repr__(self):
        args_repr = ', '.join(name_or_repr(arg) for arg in self.args)
        return self.__class__.__name__ + '(' + args_repr + ')'


#: A singleton  indicating that a callable's return value should be
#: stored based on the type of that return value.
result_type = returns_result_type()


class Nothing(RequiresType, returns):

    def process(self, result):
        return ()


#: A singleton that be used as a :class:`~mush.requires` to indicate that a
#: callable has no required arguments or as a :class:`~mush.returns` to indicate
#: that anything returned from a callable should be ignored.
nothing = Nothing()


class DeclarationsFrom(Enum):
    original = auto()
    replacement = auto()


#: Use declarations from the original callable.
original = DeclarationsFrom.original
#: Use declarations from the replacement callable.
replacement = DeclarationsFrom.replacement


VALID_DECORATION_TYPES = (type, str, Value, Requirement)


def valid_decoration_types(*objs):
    for obj in objs:
        if not isinstance(obj, VALID_DECORATION_TYPES):
            raise TypeError(
                repr(obj)+" is not a type or label"
            )
