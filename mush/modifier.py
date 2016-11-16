"""
.. currentmodule:: mush
"""

from .callpoints import CallPoint
from .markers import not_specified


class Modifier(object):
    """
    Used to make changes at a particular point in a runner.
    These are returned by :meth:`Runner.add` and :meth:`Runner.__getitem__`.
    """
    def __init__(self, runner, callpoint, label=None):
        self.runner = runner
        self.callpoint = callpoint
        if label is not_specified:
            self.labels = set()
        elif label:
            self.labels = {label}
        elif self.callpoint:
            self.labels = set(self.callpoint.labels)
        else:
            self.labels = set()

    def add(self, obj, requires=None, returns=None, label=None):
        """
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

        If no label is specified but the point which this
        :class:`~.modifier.Modifier` represents has any labels, those labels
        will be moved to the newly inserted point.
        """
        if label in self.runner.labels:
            raise ValueError('%r already points to %r' % (
                label, self.runner.labels[label]
            ))
        callpoint = CallPoint(obj, requires, returns)

        if label:
            self.add_label(label, callpoint)

        callpoint.previous = self.callpoint

        if self.callpoint:

            callpoint.next = self.callpoint.next
            if self.callpoint.next:
                self.callpoint.next.previous = callpoint
            self.callpoint.next = callpoint

            if not label:
                for label in self.labels:
                    self.add_label(label, callpoint)
                    callpoint.added_using.add(label)
        else:
            self.runner.start = callpoint

        if self.callpoint is self.runner.end or self.runner.end is None:
            self.runner.end = callpoint

        self.callpoint = callpoint

    def add_label(self, label, callpoint=None):
        """
        Add a label to the point represented by this
        :class:`~.modifier.Modifier`.

        :param callpoint: For internal use only.
        """
        callpoint = callpoint or self.callpoint
        callpoint.labels.add(label)
        old_callpoint = self.runner.labels.get(label)
        if old_callpoint:
            old_callpoint.labels.remove(label)
        self.runner.labels[label] = callpoint
        self.labels.add(label)
