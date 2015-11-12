from .context import Context, ContextError
from .modifier import Modifier
from mush import not_specified
from mush.callpoints import CallPoint


class Runner(object):

    start = end = None

    def __init__(self, *objects):
        self.labels = {}
        self.extend(*objects)

    def append(self, obj, requires=None, returns=None, label=None):
        """
        Add a callable to the runner.
        """
        m = Modifier(self, self.end, not_specified)
        m.append(obj, requires, returns, label)
        return m

    def _copy_from(self, start_point, end_point):
        previous_cloned_point = self.end
        point = start_point

        while point:
            cloned_point = CallPoint(point.obj, point.requires, point.returns)
            cloned_point.labels = set(point.labels)
            for label in cloned_point.labels:
                self.labels[label] = cloned_point

            if self.start is None:
                self.start = cloned_point

            if previous_cloned_point:
                previous_cloned_point.next = cloned_point
            cloned_point.previous = previous_cloned_point

            point = point.next
            previous_cloned_point = cloned_point

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
                self.append(obj)

    def clone(self, start_label=None, end_label=None):
        runner = Runner()
        runner._copy_from(
            self.labels[start_label] if start_label else self.start,
            self.labels[end_label] if end_label else self.end
        )
        return runner

    def replace(self, original, replacement):
        """
        Replace all instances of one callable with another.

        No changes in requirements or call ordering will be made.
        """
        point = self.start
        while point:
            if point.obj is original:
                point.obj = replacement
            point = point.next

    def __getitem__(self, label):
        return Modifier(self, self.labels[label], label)

    def __add__(self, other):
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
        :class:`Context` will be created meaning that no required
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
            except (ContextError, TypeError) as e:
                raise ContextError(str(e), point, context)

            if getattr(result, '__enter__', None):
                with result as manager:
                    if manager not in (None, result):
                        context.add(manager, manager.__class__)
                    result = None
                    result = self(context)

        return result


