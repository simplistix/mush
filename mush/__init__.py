from collections import defaultdict
from types import MethodType

type_func = type

class Context(dict):

    def add(self, it, type=None):
        type = type or type_func(it)
        if type in self:
            raise ValueError('Context already contains %s' % (
                    type.__name__
                    ))
        self[type] = it

    def get(self, type):
        obj = super(Context, self).get(type)
        if obj is None:
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
    def __init__(self, type):
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

class Runner(list):

    def __init__(self, *objs):
        self.seen = set()
        self.types = [None]
        self.callables = defaultdict(Periods)
        for obj in objs:
            self.add(obj)

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
            if name is None:
                clean_args.append(t)
            else:
                clean_kw[name]=t
        if period is None:
            period = self.callables[None].normal
        period.append((Requirements(*clean_args, **clean_kw), obj))

    def __call__(self):
        context = Context()
        for key in self.types:
            for requirements, obj in self.callables[key]:
                args = []
                kw = {}
                for name, type in requirements:
                    try:
                        o = context.get(type)
                    except KeyError, e:
                        raise KeyError('%s attempting to call %r' % (e, obj))
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
                    else:
                        context.add(result)
