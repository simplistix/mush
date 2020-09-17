class ResourceKey(tuple):

    def __new__(cls, type_, identifier):
        return tuple.__new__(cls, (type_, identifier))

    @property
    def type(self):
        return self[0]

    @property
    def identifier(self):
        return self[1]

    def __str__(self):
        if self.type is None:
            return repr(self.identifier)
        elif self.identifier is None:
            return repr(self.type)
        return f'{self.type!r}, {self.identifier!r}'


class Provider:
    pass


class Resource:

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return repr(self.obj)
