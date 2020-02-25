import asyncio
from functools import partial

from mush import Context
from mush.declarations import ResourceKey


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

    def __init__(self):
        super().__init__()
        self._sync_context = SyncContext(self, asyncio.get_event_loop())

    def _context_for(self, obj):
        return self if asyncio.iscoroutinefunction(obj) else self._sync_context

    async def get(self, key: ResourceKey, default=None):
        resolvable = self._get(key, default)
        r = resolvable.resolver
        if r is not None:
            return await ensure_async(r, self._context_for(r), default)
        return resolvable.value

    async def call(self, obj, requires=None):
        args = []
        kw = {}
        resolving = self._resolve(obj, requires, args, kw, self._context_for(obj))
        for requirement in resolving:
            r = requirement.resolve
            if r is not None:
                o = await ensure_async(r, self._context_for(r))
            else:
                o = await self.get(requirement.key, requirement.default)
            resolving.send(o)
        return await ensure_async(obj, *args, **kw)

    async def extract(self, obj, requires, returns):
        result = await self.call(obj, requires)
        for type, obj in returns.process(result):
            self.add(obj, type)
        return result
