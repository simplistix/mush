from . import not_specified

NONE_TYPE = None.__class__


class Context(dict):
    "Stores resources for a particular run."

    def add(self, it, type):
        """
        Add a resource to the context.

        Optionally specify the type to use for the object rather than
        the type of the object itself.
        """

        if type is NONE_TYPE:
            raise ValueError('Cannot add None to context')
        if type in self:
            raise ValueError('Context already contains %r' % (
                    type
                    ))
        self[type] = it

    def __getitem__(self, type):
        """
        Get an object of the specified type from the context.

        This will raise a :class:`KeyError` if no object of that type
        can be located.
        """
        if type is NONE_TYPE:
            return None
        obj = super(Context, self).get(type, not_specified)
        if obj is not_specified:
            raise KeyError('No %r in context' % type)
        return obj

    def __repr__(self):
        return '<Context: %s>' % super(Context, self).__repr__()
