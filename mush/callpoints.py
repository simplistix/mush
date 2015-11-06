from .declarations import result_type, nothing


class CallPoint(object):

    next = None
    previous = None

    def __init__(self, obj, requires=None, returns=None):
        self.obj = obj
        self.requires = (requires or
                         getattr(obj, '__mush_requires__', None) or
                         nothing)
        self.returns = (returns or
                        getattr(obj, '__mush_returns__', None) or
                        result_type)
        self.labels = set()

    def __call__(self, context):
        return context.call(self.obj, self.requires, self.returns)

    def __repr__(self):
        txt = '%r %r %r' % (self.obj, self.requires, self.returns)
        if self.labels:
            txt += (' <-- ' + ', '.join(sorted(self.labels)))
        return txt
