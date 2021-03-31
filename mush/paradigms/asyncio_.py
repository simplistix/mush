import asyncio
from functools import partial
from typing import Callable

from .paradigm import Paradigm
from ..typing import Calls


class AsyncIO(Paradigm):

    def claim(self, obj: Callable) -> bool:
        if asyncio.iscoroutinefunction(obj):
            return True

    async def process(self, calls: Calls):
        call = next(calls)
        try:
            while True:
                result = await call.obj(*call.args, **call.kw)
                call = calls.send(result)
        except StopIteration:
            return result


async def asyncio_to_normal(obj, *args, **kw):
    loop = asyncio.get_event_loop()
    obj_ = partial(obj, *args, **kw)
    return await loop.run_in_executor(None, obj_)
