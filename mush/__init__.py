from collections import defaultdict

type_func = type

class Thing(object):

    def __init__(self, it, type=None):
        self.it = it
        if type is None:
            self.type = type_func(it)
        else:
            self.type = type

    def __repr__(self):
        return '<Thing (%r): type=%s>' % (
            self.it, self.type.__name__
            )

class Context(dict):

    def add(self, thing):
        if not isinstance(thing, Thing):
            raise TypeError('Can only add Thing instances to Contexts')
        if thing.type in self:
            raise ValueError('Context already contains %s' % (
                    thing.type.__name__
                    ))
        self[thing.type] = thing

    def get(self, type):
        obj = super(Context, self).get(type)
        if obj is None:
            raise KeyError('No %s in context' % type.__name__)
        return obj.it

    def __repr__(self):
        return '<Context: (%s)>' % (', '.join(
            repr(thing) for key, thing in sorted(self.items())
            ))

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
                    if not isinstance(result, (tuple, list)):
                        result = (result, )
                    for obj in result:
                        if not isinstance(obj, Thing):
                            obj = Thing(obj)
                        context.add(obj)
