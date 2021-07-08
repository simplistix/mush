from functools import partial
from importlib import import_module
from typing import Callable, List, Optional, Dict, Tuple

from .paradigm import Paradigm, MissingParadigm



def missing_shifter(exception, obj):
    raise exception


class Paradigms:

    def __init__(self):
        self._paradigms: List[Paradigm] = []
        self._shifters: Dict[Tuple['Paradigm', 'Paradigm'], Callable] = {}

    def register(self, paradigm: Paradigm) -> None:
        self._paradigms.insert(0, paradigm)

    def register_if_possible(self, module_path: str, class_name: str) -> Paradigm:
        try:
            module = import_module(module_path)
        except ModuleNotFoundError as e:
            paradigm = MissingParadigm(e)
        else:
            paradigm = getattr(module, class_name)()
        self.register(paradigm)
        return paradigm

    def add_shifter_if_possible(
            self, source: Paradigm, target: Paradigm, module_path: str, callable_name: str
    ) -> None:
        try:
            module = import_module(module_path)
        except ModuleNotFoundError as e:
            shifter = partial(missing_shifter, e)
        else:
            shifter = getattr(module, callable_name)
        self._shifters[source, target] = shifter

    def find_paradigm(self, obj: Callable) -> Paradigm:
        for paradigm in self._paradigms:
            if paradigm.claim(obj):
                return paradigm
        raise Exception('No paradigm')

    def find_caller(self, obj: Callable, target_paradigm: Paradigm) -> Callable:
        source_paradigm = self.find_paradigm(obj)
        if source_paradigm is target_paradigm:
            return obj
        else:
            return partial(self._shifters[source_paradigm, target_paradigm], obj)
