class Plug(object):
    """
    Base class for a 'Plug' that can add to several points in a runner.
    """

    def add_to(self, runner):
        """
        Add other methods of the instance to the supplied runner.
        The name of the method will be used as the label in the runner
        at which the method will be added.

        If no such label exists, a :class:`KeyError` will be raised.
        """
        for name in dir(self):
            if not (name.startswith('_') or name == 'add_to'):
                runner[name].add(getattr(self, name))
