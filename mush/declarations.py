import sys
import types
from .markers import missing


def name_or_repr(obj):
    return getattr(obj, '__name__', None) or repr(obj)


class requires(object):
    """
    Represents requirements for a particular callable.

    The passed in `args` and `kw` should map to the types, including
    any required :class:`~.declarations.how`, for the matching
    arguments or keyword parameters the callable requires.

    String names for resources must be used instead of types where the callable
    returning those resources is configured to return the named resource.
    """

    def __init__(self, *args, **kw):
        check_type(*args)
        check_type(*kw.values())
        self.args = args
        self.kw = kw

    def __iter__(self):
        """
        When iterated over, yields tuples representing individual
        types required by arguments or keyword parameters in the form
        ``(keyword_name, decorated_type)``.

        If the keyword name is ``None``, then the type is for
        a positional argument.
        """
        for arg in self.args:
            yield None, arg
        for k, v in self.kw.items():
            yield k, v

    def __repr__(self):
        bits = []
        for arg in self.args:
            bits.append(name_or_repr(arg))
        for k, v in sorted(self.kw.items()):
            bits.append('%s=%s' % (k, name_or_repr(v)))
        txt = 'requires(%s)' % ', '.join(bits)
        return txt

    def __call__(self, obj):
        obj.__mush_requires__ = self
        return obj


class returns_result_type(object):
    """
    Default declaration that indicates a callable's return value
    should be used as a resource based on the type of the object returned.

    ``None`` is ignored as a return value.
    """

    def __call__(self, obj):
        obj.__mush_returns__ = self
        return obj

    def process(self, obj):
        if obj is not None:
            yield obj.__class__, obj

    def __repr__(self):
        return self.__class__.__name__ + '()'


class returns_mapping(returns_result_type):
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
    Declaration that specified names for returned resources or overrides
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

class optional(how):
    """
    A :class:`~.declarations.how` that indicates the callable requires the
    wrapped requirement only if it's present in the :class:`~.context.Context`.
    """
    type_pattern = 'optional(%(type)s)'

    def process(self, o):
        if o is missing:
            return nothing
        return o


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


if sys.version_info[0] == 2:
    ok_types = (type, types.ClassType, str, how)
else:
    ok_types = (type, str, how)


def check_type(*objs):
    for obj in objs:
        if not isinstance(obj, ok_types):
            raise TypeError(
                repr(obj)+" is not a type or label"
            )


#: A singleton :class:`requires` indicating that a callable
#: has no required arguments.
nothing = requires()

#: A singleton  indicating that a callable's return value should be
#: stored based on the type of that return value
result_type = returns_result_type()
