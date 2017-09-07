from .callpoints import CallPoint
from .context import Context, ContextError
from .declarations import extract_declarations
from .markers import not_specified
from .modifier import Modifier
from .plug import Plug


class Runner(object):
    """
    A chain of callables along with declarations of their required and
    returned resources along with tools to manage the order in which they
    will be called.
    """

    start = end = None

    def __init__(self, *objects):
        self.labels = {}
        self.extend(*objects)

    def add(self, obj, requires=None, returns=None, label=None):
        """
        Add a callable to the runner.

        :param obj: The callable to be added.

        :param requires: The resources to required as parameters when calling
                         `obj`. These can be specified by passing a single
                         type, a string name or a :class:`requires` object.

        :param returns: The resources that `obj` will return.
                        These can be specified as a single
                        type, a string name or a :class:`returns`,
                        :class:`returns_mapping`, :class:`returns_sequence`
                        object.

        :param label: If specified, this is a string that adds a label to the
                      point where `obj` is added that can later be retrieved
                      with :meth:`Runner.__getitem__`.
        """
        if isinstance(obj, Plug):
            obj.add_to(self)
        else:
            m = Modifier(self, self.end, not_specified)
            m.add(obj, requires, returns, label)
            return m

    def add_label(self, label):
        """
        Add a label to the the point currently at the end of the runner.
        """
        m = Modifier(self, self.end, not_specified)
        m.add_label(label)
        return m

    def _copy_from(self, start_point, end_point, added_using=None):
        previous_cloned_point = self.end
        point = start_point

        while point:
            if added_using is None or added_using in point.added_using:
                cloned_point = CallPoint(point.obj, point.requires, point.returns)
                cloned_point.labels = set(point.labels)
                for label in cloned_point.labels:
                    self.labels[label] = cloned_point

                if self.start is None:
                    self.start = cloned_point

                if previous_cloned_point:
                    previous_cloned_point.next = cloned_point
                cloned_point.previous = previous_cloned_point

                previous_cloned_point = cloned_point

            point = point.next
            if point and point.previous is end_point:
                break

        self.end = previous_cloned_point

    def extend(self, *objs):
        """
        Add the specified callables to this runner.

        If any of the objects passed is a :class:`Runner`, the contents of that
        runner will be added to this runner.
        """
        for obj in objs:
            if isinstance(obj, Runner):
                self._copy_from(obj.start, obj.end)
            else:
                self.add(obj)

    def clone(self,
              start_label=None, end_label=None,
              include_start=False, include_end=False,
              added_using=None):
        """
        Return a copy of this :class:`Runner`.

        :param start_label:
            An optional string specifying the point at which to start cloning.

        :param end_label:
            An optional string specifying the point at which to stop cloning.

        :param include_start:
            If ``True``, the point specified in ``start_label`` will be included
            in the cloned runner.

        :param include_end:
            If ``True``, the point specified in ``end_label`` will be included
            in the cloned runner.

        :param added_using:
            An optional string specifying that only points added using the
            label specified in this option should be cloned.
            This filtering is applied in addition to the above options.
        """
        runner = Runner()

        if start_label:
            start = self.labels[start_label]
            if not include_start:
                start = start.next
        else:
            start = self.start

        if end_label:
            end = self.labels[end_label]
            if not include_end:
                end = end.previous
        else:
            end = self.end

        # check start point is before end_point
        point = start.previous
        while point:
            if point is end:
                return runner
            point = point.previous

        runner._copy_from(start, end, added_using)
        return runner

    def replace(self, original, replacement, requires=None, returns=None):
        """
        Replace all instances of one callable with another.

        No changes in requirements or call ordering will be made unless the
        replacements has been decorated with and requirements, or either
        ``requires`` or ``returns`` have been specified.

        :param requires: The resources to required as parameters when calling
                         `obj`. These can be specified by passing a single
                         type, a string name or a :class:`requires` object.

        :param returns: The resources that `obj` will return.
                        These can be specified as a single
                        type, a string name or a :class:`returns`,
                        :class:`returns_mapping`, :class:`returns_sequence`
                        object.
        """
        point = self.start
        while point:
            if point.obj is original:

                new_requirements = extract_declarations(
                    replacement, requires, returns, guess=False
                )

                if any(new_requirements):
                    new_point = CallPoint(replacement, *new_requirements)
                    if point.previous is None:
                        self.start = new_point
                    else:
                        point.previous.next = new_point
                    if point.next is None:
                        self.end = new_point
                    else:
                        point.next.previous = new_point
                    new_point.next = point.next
                    for label in point.labels:
                        self.labels[label] = new_point
                        new_point.labels.add(label)
                    new_point.added_using = set(point.added_using)

                else:

                    point.obj = replacement

            point = point.next

    def __getitem__(self, label):
        """
        Retrieve a :class:`~.modifier.Modifier` for a previous labelled point in
        the runner.
        """
        return Modifier(self, self.labels[label], label)

    def __add__(self, other):
        """
        Return a new :class:`Runner` containing the contents of the two
        :class:`Runner` instances being added together.
        """
        runner = Runner()
        for r in self, other:
            runner._copy_from(r.start, r.end)
        return runner

    def __call__(self, context=None):
        """
        Execute the callables in this runner in the required order
        storing objects that are returned and providing them as
        arguments or keyword parameters when required.

        A runner may be called multiple times. Each time a new
        :class:`~.context.Context` will be created meaning that no required
        objects are kept between calls and all callables will be
        called each time.

        :param context:
          Used for passing a context when context managers are used.
          You should never need to pass this parameter.
        """
        if context is None:
            context = Context()
            context.point = self.start

        result = None

        while context.point:

            point = context.point
            context.point = point.next

            try:
                result = point(context)
            except ContextError as e:
                raise ContextError(str(e), point, context)

            if getattr(result, '__enter__', None):
                with result as manager:
                    if manager not in (None, result):
                        context.add(manager, manager.__class__)
                    result = None
                    result = self(context)

        return result

    def __repr__(self):
        bits = []
        point = self.start
        while point:
            bits.append('\n    ' + repr(point))
            point = point.next
        if bits:
            bits.append('\n')
        return '<Runner>%s</Runner>' % ''.join(bits)


