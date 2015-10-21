from collections import defaultdict, deque
import sys

type_func = lambda obj: obj.__class__
none_type = type_func(None)

markers = {}

class Marker(type):
    "Type for Marker classes"
    def __repr__(self):
        return '<Marker: %s>' % self.__name__

def marker(name):
    "Return a :class:`Marker` for the given `name`, creating if needed."
    if name not in markers:
        markers[name] = Marker(name, (object,), {})
    return markers[name]

not_specified = marker('not_specified')

class Context(dict):
    "Stores requirements, callables and resources for a particular run."
    def __init__(self):
        self.req_objs = []
        self.index = 0

    def add(self, it, type=None):
        """
        Add a resource to the context.
        
        Optionally specify the type to use for the object rather than
        the type of the object itself.
        """
        
        type = type or type_func(it)
        if type is none_type:
            raise ValueError('Cannot add None to context')
        if type in self:
            raise ValueError('Context already contains %s' % (
                    type.__name__
                    ))
        self[type] = it

    def __iter__(self):
        """
        When iterated over, the context will yield tuples containing
        the requirements for a callable and the callable itself in the
        form ``(requirements, object)``.

        This can only be done once for a given context.
        A context that has been partially iterated over will remember
        where it had got to and pick up from there when iteration
        begins again.
        """
        while self.index < len (self.req_objs):
            self.index += 1
            yield self.req_objs[self.index-1]

    def get(self, type):
        """
        Get an object of the specified type from the context.

        This will raise a :class:`KeyError` if no object of that type
        can be located.
        """
        if type is none_type:
            return None
        obj = super(Context, self).get(type, not_specified)
        if obj is not_specified:
            raise KeyError('No %s in context' % type.__name__)
        return obj

    def __repr__(self):
        return '<Context: %s>' % super(Context, self).__repr__()

class Requirements(object):
    """
    Represents requirements for a particular callable

    The passed in `args` and `kw` should map to the types, including
    any required :class:`when` or :class:`how`, for the matching
    arguments or keyword parameters the callable requires.
    """

    #: An override for the type that this callable will return.
    returns = not_specified

    def __init__(self, *args, **kw):
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
            bits.append(arg.__name__)
        for k, v in sorted(self.kw.items()):
            bits.append('%s=%s' % (k, v.__name__))
        txt = 'Requirements(%s)' % ', '.join(bits)
        if self.returns is not not_specified:
            txt += ' -> '+str(self.returns.__name__)
        return txt

#: A singleton :class:`Requirements` indicating that a callable
#: requires no resources.
nothing = Requirements()

class requires(object):
    """
    A decorator used for marking a callable with the
    :class:`Requirements` it needs.

    These are stored in an attribute called ``__requires__`` on the
    callable meaning that the callable can be used in its original
    form after decoration.

    If you need to specify requirements for a callable that cannot
    have attributes added to it, then use the :meth:`~Runner.add`
    method to do so.
    """
    def __init__(self, *args, **kw):
        self.__requires__ = Requirements(*args, **kw)

    def __call__(self, obj):
        current = getattr(obj, '__requires__', None)
        if current is None:
            obj.__requires__ = self.__requires__
        else:
            kw = dict(current.kw)
            kw.update(self.__requires__.kw)
            obj.__requires__ = Requirements(
                *(current.args + self.__requires__.args),
                **kw
                )
        return obj

class returns(object):
    """
    A decorator to indicate that a callable should be treated as
    returning the type passed to :meth:`returns` rather than the
    type of the actual return value.
    """
    def __init__(self, type):
        self.type = type

    def __call__(self, obj):
        obj.__returns__ = self.type
        return obj

class when(object):
    """
    The base class for type decorators that indicate when a callable
    requires a particular type.

    :param type: The type to be decorated.
    """
    def __init__(self, type=none_type):
        self.type = type
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.type.__name__)
    @property
    def __name__(self):
        return repr(self)

class first(when):
    """
    A :class:`when` that indicates the callable requires first use
    of the decorated type.
    """

class last(when):
    """
    A :class:`when` that indicates the callable requires last use
    of the decorated type.
    """

class how(object):
    """
    The base class for type decorators that indicate which part of a
    resource is required by a particular callable.

    :param type: The type to be decorated.
    :param name: The part of the type required by the callable.
    """
    type_pattern = '%(type)s'
    name_pattern = ''

    def __init__(self, type, *names):
        self.type = type
        self.names = names

    def __repr__(self):
        txt = self.type_pattern % dict(type=self.type.__name__)
        for name in self.names:
            txt += self.name_pattern % dict(name=name)
        return txt

    @property
    def __name__(self):
        return repr(self)
    
class attr(how):
    """
    A :class:`how` that indicates the callable requires the named
    attribute from the decorated type.
    """
    name_pattern = '.%(name)s'
    def op(self, o):
        for name in self.names:
            o = getattr(o, name)
        return o

class item(how):
    """
    A :class:`how` that indicates the callable requires the named
    item from the decorated type.
    """
    name_pattern = '[%(name)r]'
    def op(self, o):
        for name in self.names:
            o = o[name]
        return o

class ignore(how):
    """
    A :class:`how` that indicates the callable should not be passed
    an object of the decorated type.
    """
    type_pattern = 'ignore(%(type)s)'
    @staticmethod
    def op(o):
        return nothing

def after(type):
    """
    A type wrapper that specifies the callable marked as requiring this type
    should not be passed an object of this type but should only be called
    once an object of that type is available, and should be done so in the
    ``last`` period.
    """
    return last(ignore(type))

class Periods(object):
    """
    A collection of lists used to store the callables that require a
    particular resource type.
    """
    
    def __init__(self):
        #: The callables that require first use of a particular resource.
        self.first = []
        #: The callables that require use of a particular resource in
        #: the order to which they're added to the :class:`Runner`.
        self.normal = []
        #: The callables that require last use of a particular resource.
        self.last = []
        
    def __iter__(self):
        """
        Yields callables in the order in which they require the
        resource this instance is used for.
        """
        for obj in self.first:
            yield obj
        for obj in self.normal:
            yield obj
        for obj in self.last:
            yield obj

    def __repr__(self):
        return '<Periods first:%r normal:%r last:%r>' % (
            self.first, self.normal, self.last
            )

class Runner(object):
    """
    Used to run callables in the order in which they require
    particular resources and then, having taken that into account, in
    the order they are added to the runner.

    :param objs: The callables to add to the runner as it is created.
    :param debug:
       If passed, debug information will be written whenever an object
       is added to the runner. If ``True``, it will be written to
       :obj:`~sys.stderr`. A file-like object can also be passed, in
       which case the information will be written to that object.
    """
    
    def __init__(self, *objs, **debug):
        self.debug = debug.pop('debug', False)
        self.types = [none_type]
        self.callables = defaultdict(Periods)
        self.extend(*objs)

    def _debug(self, message, *args):
        if getattr(self.debug, 'write', None):
            debug = self.debug
        else:
            debug = sys.stderr
        debug.write(message % args + '\n')

    def _merge(self, other):
        self.types = list(other.types)
        for type, source in other.callables.items():
            target = self.callables[type]
            for name, contents in vars(source).items():
                getattr(target, name).extend(contents)
        self.debug = self.debug or other.debug
        
    def clone(self):
        "Return a copy of this runner."
        c = Runner()
        c._merge(self)
        return c

    def __add__(self, other):
        """
        Concatenate two runners, returning a new runner.

        The order of the new runner is as if the callables had been
        added in order from runner on the left-hand side of expression
        and then in order from the runner on the right-hand side of
        the expression.
        """
        runner = Runner()
        for r in self, other:
            runner._merge(r)
        return runner

    def add_returning(self, obj, returns, *args, **kw):
        """
        Add a callable to the runner and specify that it should
        be treated as returning the type specified in ``returns``,
        regardless of the actual type returned by calling ``obj``.

        If either ``args`` or ``kw`` are specified, they will be used
        to create the :class:`Requirements` in this runner for the
        callable added in favour of any decoration done with
        :class:`requires`.
        """
        if args or kw:
            requirements = Requirements(*args, **kw)
        else:
            requirements = getattr(obj, '__requires__', nothing)

        if returns is not_specified:
            returns = getattr(obj, '__returns__', not_specified)

        clean_args = []
        clean_kw = {}

        period_name = 'normal'
        type_index = 0
        for name, wrapped_type in requirements:
            req_period = 'normal'
            type = wrapped_type
            while isinstance(type, (when, how)):
                if isinstance(type, when):
                    req_period = type.__class__.__name__
                type = type.type
                
            if type not in self.types:
                self.types.append(type)

            req_type_index = self.types.index(type)
            if req_type_index >= type_index:
                period_name = req_period
                type_index = req_type_index
                
            if type is none_type:
                continue
                
            if name is None:
                clean_args.append(wrapped_type)
            else:
                clean_kw[name]=wrapped_type

        order_type = self.types[type_index]
        period = getattr(self.callables[order_type], period_name)

        clean = Requirements(*clean_args, **clean_kw)
        clean.returns = returns

        period.append((clean, requirements, obj))
        if self.debug:
            self._debug('Added %r to %r period for %r with %r',
                        obj, period_name, order_type, clean)
            self._debug('Current call order:')
            for key in self.types:
                self._debug('For %r:', key)
                periods = self.callables[key]
                for period in 'first', 'normal', 'last':
                    callables = getattr(periods, period)
                    for req, _, obj in callables:
                        self._debug('%8s: %r requires %r',
                                    period, obj, req)
            self._debug('')

    def add(self, obj, *args, **kw):
        """
        Add a callable to the runner.

        If either ``args`` or ``kw`` are specified, they will be used
        to create the :class:`Requirements` in this runner for the
        callable added in favour of any decoration done with
        :class:`requires`.
        """
        return self.add_returning(obj, not_specified, *args, **kw)

    def __iter__(self):
        for key in self.types:
            for req_obj in self.callables[key]:
                yield req_obj
        
    def extend(self, *objs):
        """
        Add the specified callables to this runner.

        If any of the objects passed is a :class:`Runner`, the contents of that
        runner will be added to this runner.
        """
        for obj in objs:
            if isinstance(obj, Runner):
                for _, reqs, o in obj:
                    self.add(o, *reqs.args, **reqs.kw)
            else:
                self.add(obj)

    def replace(self, original, replacement):
        """
        Replace all instances of one callable with another.

        No changes in requirements or call ordering will be made.
        """
        for period in self.callables.values():
            for l in period.first, period.normal, period.last:
                for i, req_obj in enumerate(l):
                    clean, req, obj = req_obj
                    if obj is original:
                        l[i] = (clean, req, replacement)
    
    def __call__(self, context=None):
        """
        Execute the callables in this runner in the required order
        storing objects that are returned and providing them as
        arguments or keyword parameters when required.

        A runner may be called multiple times. Each time a new
        :class:`Context` will be created meaning that no required
        objects are kept between calls and all callables will be
        called each time.
        
        :param context:
          Used for passing a context when context managers are used.
          You should never need to pass this parameter.
        """
        if context is None:
            context = Context()
            for req, _, obj in self:
                context.req_objs.append((req, obj))
            
        for requirements, obj in context:

            args = []
            kw = {}
            for name, type in requirements:

                ops = deque()
                while isinstance(type, (when, how)):
                    if isinstance(type, how):
                        ops.appendleft(type.op)
                    type = type.type

                try:
                    o = context.get(type)
                except KeyError as e:
                    raise KeyError('%s attempting to call %r' % (e, obj))

                for op in ops:
                    o = op(o)

                if o is nothing:
                    pass
                elif name is None:
                    args.append(o)
                else:
                    kw[name] = o

            result = obj(*args, **kw)

            if requirements.returns is not not_specified:
                context.add(result, requirements.returns)
            elif result is not None:
                if type_func(result) in (tuple, list):
                    for obj in result:
                        context.add(obj)
                elif type_func(result) is dict:
                    for type, obj in result.items():
                        context.add(obj, type)
                elif getattr(result, '__enter__', None):
                    context.add(result)
                    with result as obj:
                        if obj not in (None, result):
                            context.add(obj)
                        self(context)
                else:
                    context.add(result)
