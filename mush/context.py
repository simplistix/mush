from typing import Callable

from .paradigms import Call, Paradigm, Paradigms, paradigms
from .typing import Calls


class Context:

    paradigms: Paradigms = paradigms

    def __init__(self, paradigm: Paradigm = None):
        self.paradigm = paradigm

    def _resolve(self, obj: Callable, target_paradigm: Paradigm) -> Calls:
        caller = self.paradigms.find_caller(obj, target_paradigm)
        yield Call(caller, (), {})

    def call(self, obj: Callable, *, paradigm: Paradigm = None):
        paradigm = paradigm or self.paradigm or self.paradigms.find_paradigm(obj)
        calls = self._resolve(obj, paradigm)
        return paradigm.process(calls)

