from collections import deque
from enum import Enum, auto
from functools import (
    WRAPPER_UPDATES,
    WRAPPER_ASSIGNMENTS as FUNCTOOLS_ASSIGNMENTS,
    update_wrapper as functools_update_wrapper,
)
from inspect import signature
from itertools import chain
from typing import Type, Callable, NewType, Union, Any

from .markers import missing

ResourceKey = NewType('ResourceKey', Union[Type, str])
ResourceValue = NewType('ResourceValue', Any)
Resolver = Callable[['Context', Any], ResourceValue]


def name_or_repr(obj):
    return getattr(obj, '__name__', None) or repr(obj)


def set_mush(obj, key, value):
    if not hasattr(obj, '__mush__'):
        obj.__mush__ = {}
    obj.__mush__[key] = value


class Requirement:

    resolve = None

    def __init__(self, source, default=missing, target=None):
        self.repr = name_or_repr(source)
        self.target = target
        self.default = default

        self.ops = deque()
        while isinstance(source, how):
            self.ops.appendleft(source.process)
            source = source.type
        self.key: ResourceKey = source

    def __repr__(self):
        return f'{type(self).__name__}({self.repr}, default={self.default})'


class RequiresType(list):
    """
    Represents requirements for a particular callable.

    The passed in `args` and `kw` should map to the types, including
    any required :class:`~.declarations.how`, for the matching
    arguments or keyword parameters the callable requires.

    String names for resources must be used instead of types where the callable
    returning those resources is configured to return the named resource.
    """

    def __init__(self, *args, **kw):
        super().__init__()
        check_type(*args)
        check_type(*kw.values())
        for target, requirement in chain(
            ((None, arg) for arg in args),
            kw.items(),
        ):
            if isinstance(requirement, Requirement):
                requirement.target = target
            else:
                requirement = Requirement(requirement, target=target)
            self.append(requirement)

    def __repr__(self):
        parts = (r.repr if r.target is None else f'{r.target}={r.repr}'
                 for r in self)
        return f"requires({', '.join(parts)})"

    def __call__(self, obj):
        set_mush(obj, 'requires', self)
        return obj


requires = RequiresType


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
        check_type(*args)
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


class DeclarationsFrom(Enum):
    #: Use declarations from the original callable.
    original = auto()
    #: Use declarations from the replacement callable.
    replacement = auto()


original = DeclarationsFrom.original
replacement = DeclarationsFrom.replacement


class how(object):
    """
    The base class for type decorators that indicate which part of a
    resource is required by a particular callable.

    :param type: The resource type to be decorated.
    :param names: Used to identify the part of the resource to extract.
    """
    type_pattern = '%(type)s'
    name_pattern = ''

    def __init__(self, type, *names):
        check_type(type)
        self.type = type
        self.names = names

    def __repr__(self):
        txt = self.type_pattern % dict(type=name_or_repr(self.type))
        for name in self.names:
            txt += self.name_pattern % dict(name=name)
        return txt

    def process(self, o):
        """
        Extract the required part of the object passed in.
        :obj:`missing` should be returned if the required part
        cannot be extracted.
        :obj:`missing` may be passed in and is usually be handled
        by returning :obj:`missing` immediately.
        """
        return missing


class attr(how):
    """
    A :class:`~.declarations.how` that indicates the callable requires the named
    attribute from the decorated type.
    """
    name_pattern = '.%(name)s'

    def process(self, o):
        if o is missing:
            return o
        try:
            for name in self.names:
                o = getattr(o, name)
        except AttributeError:
            return missing
        else:
            return o


class item(how):
    """
    A :class:`~.declarations.how` that indicates the callable requires the named
    item from the decorated type.
    """
    name_pattern = '[%(name)r]'

    def process(self, o):
        if o is missing:
            return o
        try:
            for name in self.names:
                o = o[name]
        except KeyError:
            return missing
        else:
            return o


ok_types = (type, str, how, Requirement)


def check_type(*objs):
    for obj in objs:
        if not isinstance(obj, ok_types):
            raise TypeError(
                repr(obj)+" is not a type or label"
            )


class Nothing(requires, returns):

    def process(self, result):
        return ()


#: A singleton that be used as a :class:`~mush.requires` to indicate that a
#: callable has no required arguments or as a :class:`~mush.returns` to indicate
#: that anything returned from a callable should be ignored.
nothing = Nothing()

#: A singleton  indicating that a callable's return value should be
#: stored based on the type of that return value.
result_type = returns_result_type()


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


def extract_requires(obj, explicit=None):
    # from annotations
    by_name = {}
    for name, p in signature(obj).parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue

        if isinstance(p.default, Requirement):
            requirement = p.default
        elif isinstance(p.annotation, Requirement):
            requirement = p.annotation
        else:
            key = p.name if p.annotation is p.empty else p.annotation
            default = missing if p.default is p.empty else p.default
            requirement = Requirement(key, default=default)

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
        elif not isinstance(explicit, requires):
            requires_ = requires(explicit)
        else:
            requires_ = explicit
        _unpack_requires(by_name, by_index, requires_)

    if not by_name:
        return nothing

    args = []
    kw = {}
    for requirement in by_name.values():
        if requirement.target is None:
            args.append(requirement)
        else:
            kw[requirement.target] = requirement

    return requires(*args, **kw)


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
