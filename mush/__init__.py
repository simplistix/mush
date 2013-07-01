from collections import defaultdict

type_func = type

class Thing(object):

    def __init__(self, it, type=None, name=None, context_manager=None):
        self.it = it
        self.name = name
        if type is None:
            self.type = type_func(it)
        else:
            self.type = type
        if context_manager is None:
            self.context_manager = bool(
                getattr(it, '__enter__', None) and getattr(it, '__exit__', None)
                )
        else:
            self.context_manager = context_manager

    def __repr__(self):
        return '<Thing (%r): type=%s, name=%r, context_manager=%s>' % (
            self.it, self.type.__name__, self.name, self.context_manager
            )

class Context(dict):

    def add(self, thing):
        if not isinstance(thing, Thing):
            raise TypeError('Can only add Thing instances to Contexts')
        key = (thing.type, thing.name)
        if key in self:
            raise ValueError('%s named %r already exists' % (
                    thing.type.__name__, thing.name
                    ))
        self[key] = thing

    def get(self, type, name=None):
        obj = super(Context, self).get((type, name))
        if obj is None:
            raise KeyError('No %s named %r' % (type.__name__, name))
        return obj.it

    def __repr__(self):
        return '<Context: (%s)>' % (', '.join(
            repr(thing) for key, thing in sorted(self.items())
            ))

class Requirement(object):

    def __init__(self, type, name):
        self.type = type
        self.name = name

class requires(object):

    when = 0
    
    def __init__(self, *args, **kw):
        sargs = []
        for arg in args:
            if not isinstance(arg, Requirement):
                arg = Requirement(arg, None)
            sargs.append(arg)
        skw = {}
        for k, v in kw.items():
            if not isinstance(v, Requirement):
                v = Requirement(v, None)
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
        self.types = [(None, None)]
        self.callables = defaultdict(list)
        for obj in objs:
            self.add(obj)

    def add(self, obj):
        args_required, kw_required = getattr(obj, '__requires__', ((), {}))
        found_req = False
        for reqs in args_required, kw_required.values():
            for req in reqs:
                found_req = True
                key = req.type, req.name
                if key not in self.types:
                    self.types.append(key)
                self.callables[key].append(obj)
        if not found_req:
            self.callables[(None, None)].append(obj)

    def __call__(self):
        context = Context()
        for key in self.types:
            for obj in self.callables[key]:
                args = []
                kw = {}
                args_required, kw_required = getattr(obj, '__requires__', ((), {}))
                try:
                    for r in args_required:
                        args.append(context.get(r.type, r.name))
                    for k, r in kw_required.items():
                        kw[k] = context.get(r.type, r.name)
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
