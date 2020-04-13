from enum import Enum, auto
from itertools import chain
from typing import _type_check

from .markers import set_mush
from .requirements import Requirement, Value, name_or_repr
from .typing import RequirementType, ReturnType

VALID_DECORATION_TYPES = (type, str, Requirement)


def valid_decoration_types(*objs):
    for obj in objs:
        if isinstance(obj, VALID_DECORATION_TYPES):
            continue
        try:
            _type_check(obj, '')
            continue
        except TypeError:
            pass
        raise TypeError(
            repr(obj)+" is not a valid decoration type"
        )


class RequiresType(list):

    def __repr__(self):
        parts = (repr(r) if r.target is None else f'{r.target}={r!r}'
                 for r in self)
        return f"requires({', '.join(parts)})"

    def __call__(self, obj):
        set_mush(obj, 'requires', self)
        return obj


def requires(*args: RequirementType, **kw: RequirementType):
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
        if isinstance(possible, Requirement):
            possible = possible.make_from(possible, target=target)
            requirement = possible
        else:
            requirement = Value(possible)
            requirement.type = None if isinstance(possible, str) else possible
            requirement.name = target
            requirement.target = target
        requires_.append(requirement)
    return requires_


requires_nothing = RequiresType()


class ReturnsType(object):

    def __call__(self, obj):
        set_mush(obj, 'returns', self)
        return obj

    def __repr__(self):
        return self.__class__.__name__ + '()'


class returns(ReturnsType):
    """
    Declaration that specifies names for returned resources or overrides
    the type of a returned resource.

    This declaration can be used to indicate the type or name of a single
    returned resource or, if multiple arguments are passed, that the callable
    will return a sequence of values where each one should be named or have its
    type overridden.
    """

    def __init__(self, *args: ReturnType):
        valid_decoration_types(*args)
        self.args = args

    def process(self, obj):
        if len(self.args) == 1:
            yield self.args[0], obj
        elif self.args:
            for t, o in zip(self.args, obj):
                yield t, o

    def __repr__(self):
        args_repr = ', '.join(name_or_repr(arg) for arg in self.args)
        return self.__class__.__name__ + '(' + args_repr + ')'


class returns_result_type(ReturnsType):
    """
    Default declaration that indicates a callable's return value
    should be used as a resource based on the type of the object returned.

    ``None`` is ignored as a return value, as are context managers
    """

    def process(self, obj):
        if not (obj is None or hasattr(obj, '__enter__') or hasattr(obj, '__aenter__')):
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


returns_nothing = returns()

result_type = returns_result_type()


class DeclarationsFrom(Enum):
    original = auto()
    replacement = auto()


#: Use declarations from the original callable.
original = DeclarationsFrom.original
#: Use declarations from the replacement callable.
replacement = DeclarationsFrom.replacement
