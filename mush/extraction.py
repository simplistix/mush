from functools import (
    WRAPPER_ASSIGNMENTS as FUNCTOOLS_ASSIGNMENTS,
    WRAPPER_UPDATES,
    update_wrapper as functools_update_wrapper,
    partial
)
from inspect import signature
from typing import Callable, get_type_hints

from .declarations import (
    Parameter, Requirements, Return,
    requires_nothing
)
from .markers import missing, get_mush
from .requirements import Value, Requirement


def _apply_requires(by_name, by_index, requires_):

    for i, p in enumerate(requires_):

        if p.target is None:
            try:
                name = by_index[i]
            except IndexError:
                # case where something takes *args
                by_name[i] = p
                continue
        else:
            name = p.target

        by_name[name] = p


def extract_requires(obj: Callable) -> Requirements:
    by_name = {}

    # from annotations
    try:
        annotations = get_type_hints(obj)
    except TypeError:
        annotations = {}

    for name, p in signature(obj).parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue

        # https://bugs.python.org/issue39753:
        if isinstance(obj, partial) and p.name in obj.keywords:
            continue

        type_ = annotations.get(name)
        default = missing if p.default is p.empty else p.default

        if isinstance(default, Requirement):
            requirement = default
            default = requirement.default
        elif isinstance(p.annotation, Requirement):
            requirement = p.annotation
            default = default if requirement.default is missing else requirement.default
        else:
            requirement = Value(type_, p.name, default)

        by_name[name] = Parameter(
            requirement,
            target=p.name if p.kind is p.KEYWORD_ONLY else None,
            default=default
        )

    by_index = list(by_name)

    # from declarations
    mush_requires = get_mush(obj, 'requires', None)
    if mush_requires is not None:
        _apply_requires(by_name, by_index, mush_requires)

    if not by_name:
        return requires_nothing

    # sort out target:
    needs_target = False
    for name, parameter in by_name.items():
        if parameter.target is not None:
            needs_target = True
        elif needs_target:
            parameter.target = name

    return Requirements(by_name.values())


def extract_returns(obj: Callable, explicit: Return = None):
    return None
#     if explicit is None:
#         returns_ = get_mush(obj, 'returns', None)
#         if returns_ is None:
#             annotations = getattr(obj, '__annotations__', {})
#             returns_ = annotations.get('return')
#     else:
#         returns_ = explicit
#
#     if returns_ is None or isinstance(returns_, ReturnsType):
#         pass
#     elif isinstance(returns_, (list, tuple)):
#         returns_ = returns(*returns_)
#     else:
#         returns_ = returns(returns_)
#
#     return returns_ or result_type


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
