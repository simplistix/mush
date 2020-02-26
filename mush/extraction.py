from functools import (
    WRAPPER_ASSIGNMENTS as FUNCTOOLS_ASSIGNMENTS,
    WRAPPER_UPDATES,
    update_wrapper as functools_update_wrapper,
    partial
)
from inspect import signature, Parameter
from typing import Callable

from .declarations import (
    Value,
    requires, Requirement, RequiresType, ReturnsType,
    returns, result_type,
    nothing
)
from .markers import missing

EMPTY = Parameter.empty
#: For these types, prefer the name instead of the type.
SIMPLE_TYPES = (str, int, dict, list)


def _unpack_requires(by_name, by_index, requires_):

    for i, requirement in enumerate(requires_):
        if requirement.target is None:
            try:
                arg = by_index[i]
            except IndexError:
                # case where something takes *args
                arg = i
        else:
            arg = requirement.target
        by_name[arg] = requirement


def extract_requires(obj: Callable, explicit=None):
    # from annotations
    is_partial = isinstance(obj, partial)
    by_name = {}
    for name, p in signature(obj).parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue

        # https://bugs.python.org/issue39753:
        if is_partial and p.name in obj.keywords:
            continue

        type_ = p.annotation
        default = p.default
        if isinstance(default, Requirement):
            requirement = default
            default = EMPTY
        elif isinstance(default, Value):
            requirement = default.requirement
            default = EMPTY
        elif isinstance(p.annotation, Requirement):
            requirement = p.annotation
            type_ = requirement.type
        elif isinstance(p.annotation, Value):
            requirement = p.annotation.requirement
            type_ = requirement.type
        else:
            if not p.annotation is EMPTY:
                key = p.annotation
            else:
                key = p.name
            requirement = Requirement(key)

        requirement = requirement.clone()
        if requirement.type is None and type_ is not EMPTY and isinstance(type_, type):
            requirement.type = type_
        if requirement.default is missing and default is not EMPTY:
            requirement.default = default
        if p.kind is p.KEYWORD_ONLY:
            requirement.target = p.name
        by_name[name] = requirement

    by_index = list(by_name)

    # from declarations
    mush_declarations = getattr(obj, '__mush__', None)
    if mush_declarations is not None:
        requires_ = mush_declarations.get('requires')
        if requires_ is not None:
            _unpack_requires(by_name, by_index, requires_)

    # explicit
    if explicit is not None:
        if isinstance(explicit, (list, tuple)):
            requires_ = requires(*explicit)
        elif not isinstance(explicit, RequiresType):
            requires_ = requires(explicit)
        else:
            requires_ = explicit
        _unpack_requires(by_name, by_index, requires_)

    if not by_name:
        return nothing

    needs_target = False
    for name, requirement in by_name.items():
        if requirement.target is not None:
            needs_target = True
        elif needs_target:
            requirement = requirement.clone()
            requirement.target = requirement.name
            by_name[name] = requirement

    return RequiresType(by_name.values())


def extract_returns(obj: Callable, explicit: ReturnsType = None):
    if explicit is None:
        mush_declarations = getattr(obj, '__mush__', {})
        returns_ = mush_declarations.get('returns', None)
        if returns_ is None:
            annotations = getattr(obj, '__annotations__', {})
            returns_ = annotations.get('return')
    else:
        returns_ = explicit

    if returns_ is None or isinstance(returns_, ReturnsType):
        pass
    elif isinstance(returns_, (list, tuple)):
        returns_ = returns(*returns_)
    else:
        returns_ = returns(returns_)

    return returns_ or result_type


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
