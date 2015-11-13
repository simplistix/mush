class Marker(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Marker: %s>' % self.name


not_specified = Marker('not_specified')
missing = Marker('missing')