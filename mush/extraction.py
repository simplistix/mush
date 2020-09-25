from functools import (
    WRAPPER_ASSIGNMENTS as FUNCTOOLS_ASSIGNMENTS,
    WRAPPER_UPDATES,
    update_wrapper as functools_update_wrapper,
    partial
)
from inspect import signature, Parameter
from typing import Callable, Iterable

from .declarations import (
    requires, Requires, Returns,
    returns, result_type,
    requires_nothing
)
from .requirements import Value, Requirement
from .markers import missing, get_mush
from .typing import Requires, Returns

#: For these types, prefer the name instead of the type.
# SIMPLE_TYPES = (str, int, dict, list)
#
#
# def _apply_requires(by_name, by_index, requires_):
#
#     for i, r in enumerate(requires_):
#
#         if r.target is None:
#             try:
#                 name = by_index[i]
#             except IndexError:
#                 # case where something takes *args
#                 by_name[i] = r.make_from(r)
#                 continue
#         else:
#             name = r.target
#
#         existing = by_name[name]
#         by_name[name] = r.make_from(
#             r,
#             name=existing.name,
#             key=existing.key if r.key is None else r.key,
#             type=existing.type if r.type is None else r.type,
#             default=existing.default if r.default is missing else r.default,
#             ops=existing.ops if not r.ops else r.ops,
#             target=existing.target if r.target is None else r.target,
#         )


def extract_requires(obj: Callable) -> Iterable[Requirement]:
                     # explicit: Requires = None):
    # from annotations
    by_name = {}
    for name, p in signature(obj).parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue

    #     # https://bugs.python.org/issue39753:
    #     if isinstance(obj, partial) and p.name in obj.keywords:
    #         continue
    #
        name = p.name
        if p.annotation is not p.empty:
            type_ = p.annotation
        else:
            type_ = None

        default = missing if p.default is p.empty else p.default
        ops = []

        requirement = Value(type_, p.name, default)
    #
    #     requirement = None
    #     if isinstance(default, Requirement):
    #         requirement = default
    #         default = missing
    #     elif isinstance(p.annotation, Requirement):
    #         requirement = p.annotation
    #
    #     if requirement is None:
    #         requirement = Requirement(key)
    #         if isinstance(p.annotation, str):
    #             key = p.annotation
    #         elif type_ is None or issubclass(type_, SIMPLE_TYPES):
    #             key = name
    #         else:
    #             key = type_
    #     else:
    #         requirement = requirement.make_from(requirement)
    #         type_ = type_ if requirement.type is None else requirement.type
    #         if requirement.key is not None:
    #             key = requirement.key
    #         elif type_ is None or issubclass(type_, SIMPLE_TYPES):
    #             key = name
    #         else:
    #             key = type_
    #         default = requirement.default if requirement.default is not missing else default
    #         ops = requirement.ops
    #
    #     requirement.key = key
    #     requirement.name = name
    #     requirement.type = type_
    #     requirement.default = default
    #     requirement.ops = ops
    #
    #     if p.kind is p.KEYWORD_ONLY:
    #         requirement.target = p.name
    #

        if p.kind is p.KEYWORD_ONLY:
            requirement.target = p.name

        by_name[name] = requirement
    #
    # by_index = list(by_name)
    #
    # # from declarations
    # mush_requires = get_mush(obj, 'requires', None)
    # if mush_requires is not None:
    #     _apply_requires(by_name, by_index, mush_requires)
    #
    # # explicit
    # if explicit is not None:
    #     if isinstance(explicit, RequiresType):
    #         requires_ = explicit
    #     else:
    #         if not isinstance(explicit, (list, tuple)):
    #             explicit = (explicit,)
    #         requires_ = requires(*explicit)
    #     _apply_requires(by_name, by_index, requires_)
    #
    # if not by_name:
    #     return requires_nothing
    #
    # # sort out target and apply modifier:
    # needs_target = False
    # for name, requirement in by_name.items():
    #     requirement_ = modifier(requirement)
    #     if requirement_ is not requirement:
    #         by_name[name] = requirement = requirement_
    #     if requirement.target is not None:
    #         needs_target = True
    #     elif needs_target:
    #         requirement.target = requirement.name
    #

    return by_name.values()
    # return RequiresType(by_name.values())


# def extract_returns(obj: Callable, explicit: Returns = None):
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
#
#
# WRAPPER_ASSIGNMENTS = FUNCTOOLS_ASSIGNMENTS + ('__mush__',)
#
#
# def update_wrapper(wrapper,
#                    wrapped,
#                    assigned=WRAPPER_ASSIGNMENTS,
#                    updated=WRAPPER_UPDATES):
#     """
#     An extended version of :func:`functools.update_wrapper` that
#     also preserves Mush's annotations.
#     """
#     return functools_update_wrapper(wrapper, wrapped, assigned, updated)
