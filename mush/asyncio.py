import asyncio
from functools import partial
from typing import Type, Callable

from mush import Context
from mush.declarations import ResourceKey, Requirement, RequiresType, ReturnsType


async def ensure_async(func, *args, **kw):
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kw)
    if kw:
        func = partial(func, **kw)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


class SyncContext:

    def __init__(self, context, loop):
        self.context = context
        self.loop = loop

    def get(self, key: ResourceKey, default=None):
        coro = self.context.get(key, default)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()


class AsyncContext(Context):

    def __init__(self, default_requirement_type: Type[Requirement] = Requirement):
        super().__init__(default_requirement_type)
        self._sync_context = SyncContext(self, asyncio.get_event_loop())

    def _context_for(self, obj):
        return self if asyncio.iscoroutinefunction(obj) else self._sync_context

    async def get(self, key: ResourceKey, default=None):
        resolvable = self._get(key, default)
        r = resolvable.resolver
        if r is not None:
            return await ensure_async(r, self._context_for(r), default)
        return resolvable.value

    async def call(self, obj: Callable, requires: RequiresType = None, *, mush: bool = True):
        args = []
        kw = {}
        resolving = self._resolve(obj, requires, args, kw, self._context_for(obj), mush)
        for requirement in resolving:
            r = requirement.resolve
            if r is not None:
                o = await ensure_async(r, self._context_for(r))
            else:
                o = await self.get(requirement.key, requirement.default)
            resolving.send(o)
        return await ensure_async(obj, *args, **kw)

    async def extract(self,
                      obj: Callable,
                      requires: RequiresType = None,
                      returns: ReturnsType = None,
                      mush: bool = True):
        result = await self.call(obj, requires)
        self._process(obj, result, returns, mush)
        return result
