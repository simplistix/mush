from .declarations import result_type, nothing, extract_declarations


class CallPoint(object):

    next = None
    previous = None
    requires = nothing
    returns = result_type

    def __init__(self, obj, requires=None, returns=None):
        self.obj = obj
        requires, returns = extract_declarations(obj, requires, returns)
        self.requires = requires or nothing
        self.returns = returns or result_type
        self.labels = set()
        self.added_using = set()

    def __call__(self, context):
        return context.call(self.obj, self.requires, self.returns)

    def __repr__(self):
        txt = '%r %r %r' % (self.obj, self.requires, self.returns)
        if self.labels:
            txt += (' <-- ' + ', '.join(sorted(self.labels)))
        return txt
