from .declarations import returns as returns_declaration


class ValueResolver:
    
    __slots__ = ['value']
    
    def __init__(self, value):
        self.value = value
        
    def __call__(self, context, default):
        return self.value

    def __repr__(self):
        return repr(self.value)


class Lazy(object):

    def __init__(self, obj, requires, returns):
        if not (type(returns) is returns_declaration and len(returns.args) == 1):
            raise TypeError('a single return type must be explicitly specified')
        self.__wrapped__ = obj
        self.requires = requires
        self.provides = returns.args[0]

    def __call__(self, context):
        context.add(resolver=self.resolve, provides=self.provides)

    def resolve(self, context, default):
        result = context.call(self.__wrapped__, self.requires)
        context.remove(self.provides)
        context.add(result, self.provides)
        return result

    def __repr__(self):
        return '<Lazy for %r>' % self.__wrapped__
