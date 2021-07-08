from typing import Callable

from .paradigm import Paradigm
from ..typing import Calls


class Normal(Paradigm):

    def claim(self, obj: Callable) -> bool:
        return True

    def process(self, calls: Calls):
        call = next(calls)
        try:
            while True:
                result = call.obj(*call.args, **call.kw)
                call = calls.send(result)
        except StopIteration:
            return result
