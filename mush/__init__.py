from collections import defaultdict
from types import MethodType

type_func = lambda obj: obj.__class__
none_type = type_func(None)
marker = object()

class Context(dict):

    def __init__(self):
        self.req_objs = []
        self.index = 0

    def add(self, it, type=None):
        type = type or type_func(it)
        if type is none_type:
            raise ValueError('Cannot add None to context')
        if type in self:
            raise ValueError('Context already contains %s' % (
                    type.__name__
                    ))
        self[type] = it

    def __iter__(self):
        while self.index < len (self.req_objs):
            self.index += 1
            yield self.req_objs[self.index-1]

    def get(self, type):
        if type is none_type:
            return None
        obj = super(Context, self).get(type, marker)
        if obj is marker:
            raise KeyError('No %s in context' % type.__name__)
        return obj

    def __repr__(self):
        return '<Context: %s>' % super(Context, self).__repr__()

class Requirements(object):

    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw

    def __iter__(self):
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
        return 'Requirements(%s)' % ', '.join(bits)

nothing = Requirements()

class requires(object):

    def __init__(self, *args, **kw):
        self.__requires__ = Requirements(*args, **kw)

    def __call__(self, obj):
        obj.__requires__ = self.__requires__
        return obj

class when(object):
    def __init__(self, type=none_type):
        self.type = type
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.type.__name__)

class first(when): pass
class last(when): pass

class Periods(object):
    
    def __init__(self):
        self.first = []
        self.normal = []
        self.last = []
        
    def __iter__(self):
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

    def __init__(self, *objs):
        self.seen = set()
        self.types = [none_type]
        self.callables = defaultdict(Periods)
        self.extend(*objs)

    def _merge(self, other):
        self.seen.update(other.seen)
        self.types = list(other.types)
        for type, source in other.callables.items():
            target = self.callables[type]
            for name, contents in vars(source).items():
                getattr(target, name).extend(contents)
        
    def clone(self):
        c = Runner()
        c._merge(self)
        return c
    
    def __add__(self, other):
        runner = Runner()
        for r in self, other:
            runner._merge(r)
        return runner

    def add(self, obj, *args, **kw):
        if isinstance(obj, MethodType):
            cls = obj.im_class
            if cls not in self.types:
                self._add(cls, None, None)
            self._add(obj, args, kw, cls)
        else:
            self._add(obj, args, kw)

    def _add(self, obj, args, kw, class_=None):
        if obj in self.seen:
            return
        self.seen.add(obj)
        if args or kw:
            requirements = Requirements(*args, **kw)
        else:
            requirements = getattr(obj, '__requires__', nothing)
        clean_args = []
        clean_kw = {}
        if class_ is not None:
            clean_args.append(class_)
        period = None
        for name, type in requirements:
            if isinstance(type, when):
                t = type.type
                period = getattr(self.callables[t], type.__class__.__name__)
            else:
                t = type
                period = self.callables[t].normal
            if t not in self.types:
                self.types.append(t)
            if t is none_type:
                continue
            if name is None:
                clean_args.append(t)
            else:
                clean_kw[name]=t
        if period is None:
            period = self.callables[none_type].normal
        period.append((Requirements(*clean_args, **clean_kw), obj))
    
    def extend(self, *objs):
        for obj in objs:
            self.add(obj)

    def __call__(self, context=None):
        if context is None:
            context = Context()
            for key in self.types:
                for req_obj in self.callables[key]:
                    context.req_objs.append(req_obj)
            
        for requirements, obj in context:
            args = []
            kw = {}
            for name, type in requirements:
                try:
                    o = context.get(type)
                except KeyError, e:
                    raise KeyError('%s attempting to call %r' % (e, obj))
                if o is not None:
                    if name is None:
                        args.append(o)
                    else:
                        kw[name] = o
            result = obj(*args, **kw)
            if result is not None:
                if type_func(result) in (tuple, list):
                    for obj in result:
                        context.add(obj)
                elif type_func(result) is dict:
                    for type, obj in result.items():
                        context.add(obj, type)
                elif getattr(result, '__enter__', None):
                    context.add(result)
                    with result:
                        self(context)
                else:
                    context.add(result)
