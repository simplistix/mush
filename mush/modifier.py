from mush import not_specified
from mush.callpoints import CallPoint


class Modifier(object):

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

    def append(self, obj, requires=None, returns=None, label=None):
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
        else:
            self.runner.start = callpoint

        if self.callpoint is self.runner.end or self.runner.end is None:
            self.runner.end = callpoint

        self.callpoint = callpoint

    def add_label(self, label, callpoint=None):
        callpoint = callpoint or self.callpoint
        callpoint.labels.add(label)
        old_callpoint = self.runner.labels.get(label)
        if old_callpoint:
            old_callpoint.labels.remove(label)
        self.runner.labels[label] = callpoint
        self.labels.add(label)
