from .declarations import returns as returns_declaration


class ValueResolver:
    
    __slots__ = ['value']
    
    def __init__(self, value):
        self.value = value
        
    def __call__(self, context):
        return self.value

    def __repr__(self):
        return repr(self.value)


class Factory(object):

    value = None

    def __init__(self, obj, requires, returns):
        if not (type(returns) is returns_declaration and len(returns.args) == 1):
            raise TypeError('a single return type must be explicitly specified')
        self.__wrapped__ = obj
        self.requires = requires
        self.returns = returns

    def __repr__(self):
        return '<Factory for %r>' % self.__wrapped__
