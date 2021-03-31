from abc import ABC, abstractmethod
from typing import Callable
from ..typing import Calls


class Paradigm(ABC):

    @abstractmethod
    def claim(self, obj: Callable) -> bool:
        ...

    @abstractmethod
    def process(self, calls: Calls):
        ...


class MissingParadigm(Paradigm):

    def __init__(self, exception):
        super().__init__()
        self.exception = exception

    def claim(self, obj: Callable) -> bool:
        raise self.exception

    def process(self, calls: Calls):
        raise self.exception
