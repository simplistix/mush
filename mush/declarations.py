from enum import Enum, auto
from functools import (
    WRAPPER_ASSIGNMENTS as FUNCTOOLS_ASSIGNMENTS,
    WRAPPER_UPDATES,
    update_wrapper as functools_update_wrapper
)
from itertools import chain
from typing import _type_check, Any, List, Set

from .markers import set_mush, missing
from .requirements import Requirement, Value
from .resources import ResourceKey
from .typing import RequirementType, ReturnType, Type_

VALID_DECORATION_TYPES = (type, str, Requirement)


def check_decoration_types(*objs):
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


class Parameter:
    def __init__(self, requirement: Requirement, target: str = None,
                 type_: Type_ = None, default: Any = missing):
        self.requirement = requirement
        self.target = target
        self.default = default
        self.type = type_


class RequirementsDeclaration(List[Parameter]):

    def __call__(self, obj):
        set_mush(obj, 'requires', self)
        return obj

    def __repr__(self):
        parts = (repr(p.requirement) if p.target is None else f'{p.target}={p.requirement!r}'
                 for p in self)
        return f"requires({', '.join(parts)})"


def requires(*args: RequirementType, **kw: RequirementType):
    """
    Represents requirements for a particular callable.

    The passed in ``args`` and ``kw`` should map to the types, including
    any required :class:`~.declarations.how`, for the matching
    arguments or keyword parameters the callable requires.

    String names for resources must be used instead of types where the callable
    returning those resources is configured to return the named resource.
    """
    requires_ = RequirementsDeclaration()
    check_decoration_types(*args)
    check_decoration_types(*kw.values())
    for target, possible in chain(
        ((None, arg) for arg in args),
        kw.items(),
    ):
        if isinstance(possible, Requirement):
            parameter = Parameter(possible, target, default=possible.default)
        else:
            parameter = Parameter(Value(possible), target)
        requires_.append(parameter)
    return requires_


requires_nothing = RequirementsDeclaration()


class ReturnsDeclaration(Set[ResourceKey]):

    def __call__(self, obj):
        set_mush(obj, 'returns', self)
        return obj

    def __repr__(self):
        return f"returns({', '.join(str(k) for k in sorted(self, key=lambda o: str(o)))})"


def returns(*keys: ReturnType):
    """
    """
    check_decoration_types(*keys)
    return ReturnsDeclaration(ResourceKey.guess(k) for k in keys)


returns_nothing = ignore_return = ReturnsDeclaration()


class DeclarationsFrom(Enum):
    original = auto()
    replacement = auto()


#: Use declarations from the original callable.
original = DeclarationsFrom.original
#: Use declarations from the replacement callable.
replacement = DeclarationsFrom.replacement


WRAPPER_ASSIGNMENTS = FUNCTOOLS_ASSIGNMENTS + ('__mush__',)


def update_wrapper(wrapper,
                   wrapped,
                   assigned=WRAPPER_ASSIGNMENTS,
                   updated=WRAPPER_UPDATES):
    """
    An extended version of :func:`functools.update_wrapper` that
    also preserves Mush's annotations.
    """
    return functools_update_wrapper(wrapper, wrapped, assigned, updated)
