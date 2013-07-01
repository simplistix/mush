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

class Requirement(object):

    def __init__(self, type):
        self.type = type

class requires(object):

    when = 0
    
    def __init__(self, *args, **kw):
        sargs = []
        for arg in args:
            if not isinstance(arg, Requirement):
                arg = Requirement(arg)
            sargs.append(arg)
        skw = {}
        for k, v in kw.items():
            if not isinstance(v, Requirement):
                v = Requirement(v)
            skw[k] = v
        self.__requires__ = (sargs, skw, self.when)

    def __call__(self, obj):
        obj.__requires__ = self.__requires__
        return obj

class requires_first(requires):
    when = -1
    
class requires_last(requires):
    when = 1
    
class Runner(list):

    def __init__(self, *objs):
        self.types = [None]
        self.callables = defaultdict(list)
        for obj in objs:
            self.add(obj)

    def add(self, obj):
        args_required, kw_required, order = getattr(obj,
                                                    '__requires__',
                                                    ((), {}, 0))
        found_req = False
        for reqs in args_required, kw_required.values():
            for req in reqs:
                found_req = True
                key = req.type
                if key not in self.types:
                    self.types.append(key)
                self.callables[key].append(obj)
        if not found_req:
            self.callables[None].append(obj)

    def __call__(self):
        context = Context()
        for key in self.types:
            for obj in self.callables[key]:
                args = []
                kw = {}
                args_required, kw_required, order = getattr(obj,
                                                            '__requires__',
                                                            ((), {}, 0))
                try:
                    for r in args_required:
                        args.append(context.get(r.type))
                    for k, r in kw_required.items():
                        kw[k] = context.get(r.type)
                except KeyError, e:
                    raise KeyError('%s attempting to call %r' % (e, obj))
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
