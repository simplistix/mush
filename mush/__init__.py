from collections import defaultdict

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

nothing = Requirements()

class requires(object):

    def __init__(self, *args, **kw):
        self.__requires__ = Requirements(*args, **kw)

    def __call__(self, obj):
        obj.__requires__ = self.__requires__
        return obj

class when(object):
    def __init__(self, it):
        self.it = it
    @property
    def __name__(self):
        return self.it.__name__

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
        self.types = [None]
        self.callables = defaultdict(Periods)
        for obj in objs:
            self.add(obj)

    def add(self, obj):
        for name, type in getattr(obj, '__requires__', nothing):
            if isinstance(type, when):
                t = type.it
                period = getattr(self.callables[t], type.__class__.__name__)
                
            else:
                t = type
                period = self.callables[t].normal
            period.append(obj)
            if t not in self.types:
                self.types.append(t)
            return
        self.callables[None].normal.append(obj)

    def __call__(self):
        context = Context()
        for key in self.types:
            for obj in self.callables[key]:
                args = []
                kw = {}
                for name, type in getattr(obj, '__requires__', nothing):
                    try:
                        if isinstance(type, when):
                            type = type.it
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
