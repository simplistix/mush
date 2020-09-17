from typing import Callable, Optional

from .callpoints import CallPoint
from .context import Context, ResourceError
from .declarations import DeclarationsFrom
from .extraction import extract_requires, extract_returns
from .markers import not_specified
from .modifier import Modifier
from .plug import Plug
from .requirements import name_or_repr#, Lazy
from .typing import Requires, Returns


class Runner(object):
    """
    A chain of callables along with declarations of their required and
    returned resources along with tools to manage the order in which they
    will be called.
    """

    start: Optional[CallPoint] = None
    end: Optional[CallPoint] = None

    def __init__(self, *objects: Callable):
        self.requirement_modifier = requirement_modifier
        self.labels = {}
        self.lazy = {}
        self.extend(*objects)

    def modify_requirement(self, requirement):
        requirement = self.requirement_modifier(requirement)
        if requirement.key in self.lazy:
            requirement = Lazy(requirement, provider=self.lazy[requirement.key])
        return requirement

    def add(self, obj: Callable, requires: Requires = None, returns: Returns = None,
            label: str = None, lazy: bool = False):
        """
        Add a callable to the runner.

        :param obj: The callable to be added.

        :param requires: The resources to required as parameters when calling
                         ``obj``. These can be specified by passing a single
                         type, a string name or a :class:`requires` object.

        :param returns: The resources that ``obj`` will return.
                        These can be specified as a single
                        type, a string name or a :class:`returns`,
                        :class:`returns_mapping`, :class:`returns_sequence`
                        object.

        :param label: If specified, this is a string that adds a label to the
                      point where ``obj`` is added that can later be retrieved
                      with :meth:`Runner.__getitem__`.

        :param lazy: If true, ``obj`` will only be called the first time it
                     is needed.
        """
        if isinstance(obj, Plug):
            obj.add_to(self)
        else:
            m = Modifier(self, self.end, not_specified)
            m.add(obj, requires, returns, label, lazy)
            return m

    def add_label(self, label: str):
        """
        Add a label to the the point currently at the end of the runner.
        """
        m = Modifier(self, self.end, not_specified)
        m.add_label(label)
        return m

    def _copy_from(self, runner, start_point, end_point, added_using=None):
        if self.requirement_modifier is not runner.requirement_modifier:
            raise TypeError('requirement_modifier must be identical')

        lazy_clash = set(self.lazy) & set(runner.lazy)
        if lazy_clash:
            raise TypeError(
                'both runners have lazy providers for these resources:\n' +
                '\n'.join(f'{name_or_repr(key)}: \n'
                          f'  {self.lazy[key].obj}\n'
                          f'  {runner.lazy[key].obj}'  for key in lazy_clash)
            )
        self.lazy.update(runner.lazy)

        previous_cloned_point = self.end
        point = start_point

        while point:
            if added_using is None or added_using in point.added_using:
                cloned_point = CallPoint(self, point.obj, point.requires, point.returns)
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

    def extend(self, *objs: Callable):
        """
        Add the specified callables to this runner.

        If any of the objects passed is a :class:`Runner`, the contents of that
        runner will be added to this runner.
        """
        for obj in objs:
            if isinstance(obj, Runner):
                self._copy_from(obj, obj.start, obj.end)
            else:
                self.add(obj)

    def clone(self,
              start_label: str = None, end_label: str = None,
              include_start: bool = False, include_end: bool = False,
              added_using: str = None):
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
        runner = self.__class__(requirement_modifier=self.requirement_modifier)

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
        if start is not None:
            point = start.previous
        else:
            point = None

        while point:
            if point is end:
                return runner
            point = point.previous

        runner._copy_from(self, start, end, added_using)
        return runner

    def replace(self,
                original: Callable,
                replacement: Callable,
                requires_from: DeclarationsFrom = DeclarationsFrom.replacement,
                returns_from: DeclarationsFrom = DeclarationsFrom.original):
        """
        Replace all instances of one callable with another.

        :param original: The callable to replaced.

        :param replacement: The callable use instead.

        :param requires_from:

            Which :class:`requires` to use.
            If :attr:`~mush.declarations.DeclarationsFrom.original`,
            the existing ones will be used.
            If :attr:`~mush.declarations.DeclarationsFrom.replacement`,
            they will be extracted from the supplied replacements.

        :param returns_from:

            Which :class:`returns` to use.
            If :attr:`~mush.declarations.DeclarationsFrom.original`,
            the existing ones will be used.
            If :attr:`~mush.declarations.DeclarationsFrom.replacement`,
            they will be extracted from the supplied replacements.
        """
        point = self.start
        while point:
            if point.obj is original:
                if requires_from is DeclarationsFrom.replacement:
                    requires = extract_requires(replacement)
                else:
                    requires = point.requires
                if returns_from is DeclarationsFrom.replacement:
                    returns = extract_returns(replacement)
                else:
                    returns = point.returns

                new_point = CallPoint(self, replacement, requires, returns)

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

            point = point.next

    def __getitem__(self, label: str):
        """
        Retrieve a :class:`~.modifier.Modifier` for a previous labelled point in
        the runner.
        """
        return Modifier(self, self.labels[label], label)

    def __add__(self, other: 'Runner'):
        """
        Return a new :class:`Runner` containing the contents of the two
        :class:`Runner` instances being added together.
        """
        runner = self.__class__()
        for r in self, other:
            runner._copy_from(r, r.start, r.end)
        return runner

    def __call__(self, context: Context = None):
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
        if context.point is None:
            context.point = self.start

        result = None

        while context.point:

            point = context.point
            context.point = point.next

            try:
                result = point(context)
            except ResourceError as e:
                raise ContextError(str(e), point, context)

            if getattr(result, '__enter__', None):
                with result as managed:
                    if managed is not None:
                        context.add(managed)
                    # If the context manager swallows an exception,
                    # None should be returned, not the context manager:
                    result = None
                    if context.point is not None:
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


class ContextError(Exception):
    """
    Errors likely caused by incorrect building of a runner.
    """
    def __init__(self, text: str, point: CallPoint=None, context: Context = None):
        self.text: str = text
        self.point: CallPoint = point
        self.context: Context = context

    def __str__(self):
        rows = []
        if self.point:
            point = self.point.previous
            while point:
                rows.append(repr(point))
                point = point.previous
            if rows:
                rows.append('Already called:')
                rows.append('')
                rows.append('')
                rows.reverse()
                rows.append('')

            rows.append('While calling: '+repr(self.point))
        if self.context is not None:
            rows.append('with '+repr(self.context)+':')
            rows.append('')

        rows.append(self.text)

        if self.point:
            point = self.point.next
            if point:
                rows.append('')
                rows.append('Still to call:')
            while point:
                rows.append(repr(point))
                point = point.next

        return '\n'.join(rows)

    __repr__ = __str__
