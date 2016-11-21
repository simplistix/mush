class ignore(object):
    """
    A decorator to explicitly mark that a method of a :class:`~mush.Plug` should
    not be added to a runner by :meth:`~mush.Plug.add_to`
    """
    def __call__(self, method):
        method.__mush_plug__ = self
        return method

    def apply(self, runner, obj):
        pass


class insert(ignore):
    """
    A decorator to explicitly mark that a method of a :class:`~mush.Plug` should
    be added to a runner by :meth:`~mush.Plug.add_to`. The `label` parameter
    can be used to indicate a different label at which to add the method,
    instead of using the name of the method.
    """
    def __init__(self, label=None):
        self.label = label

    def apply(self, runner, obj):
        runner[self.label or obj.__name__].add(obj)

class append(ignore):
    """
    A decorator to mark that this method of a :class:`~mush.Plug` should
    be added to the end of a runner by :meth:`~mush.Plug.add_to`.
    """

    def apply(self, runner, obj):
        runner.add(obj)


class Plug(object):
    """
    Base class for a 'plug' that can add to several points in a runner.
    """

    #: Control whether methods need to be decorated with :class:`insert`
    #: in order to be added by this :class:`~mush.Plug`.
    explicit = False

    @ignore()
    def add_to(self, runner):
        """
        Add methods of the instance to the supplied runner.
        By default, all methods will be added and the name of the method will be
        used as the label in the runner at which the method will be added.
        If no such label exists, a :class:`KeyError` will be raised.

        If :attr:`explicit` is ``True``, then only methods decorated with an
        :class:`~mush.plug.insert` will be added.
        """

        if self.explicit:
            default_action = ignore()
        else:
            default_action = insert()

        for name in dir(self):
            if not name.startswith('_'):
                obj = getattr(self, name)
                if callable(obj):
                    action = getattr(obj, '__mush_plug__', default_action)
                    action.apply(runner, obj)
