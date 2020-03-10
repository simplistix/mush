import asyncio
from functools import partial
from typing import Callable

from . import Context as SyncContext, Call as SyncCall, missing
from .declarations import RequiresType, ReturnsType
from .extraction import default_requirement_type
from .types import RequirementModifier


async def ensure_async(func, *args, **kw):
    if getattr(func, '__nonblocking__', False):
        return func(*args, **kw)
    elif asyncio.iscoroutinefunction(func):
        return await func(*args, **kw)
    if kw:
        func = partial(func, **kw)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


class AsyncFromSyncContext:

    def __init__(self, context, loop):
        self.context = context
        self.loop = loop
        self.remove = context.remove
        self.add = context.add
        self.get = context.get

    def call(self, obj: Callable, requires: RequiresType = None):
        coro = self.context.call(obj, requires)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def extract(self, obj: Callable, requires: RequiresType = None, returns: ReturnsType = None):
        coro = self.context.extract(obj, requires, returns)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()


class Context(SyncContext):

    def __init__(self, requirement_modifier: RequirementModifier = default_requirement_type):
        super().__init__(requirement_modifier)
        self._sync_context = AsyncFromSyncContext(self, asyncio.get_event_loop())

    def _context_for(self, obj):
        return self if asyncio.iscoroutinefunction(obj) else self._sync_context

    async def call(self, obj: Callable, requires: RequiresType = None):
        args = []
        kw = {}
        resolving = self._resolve(obj, requires, args, kw, self._context_for(obj))
        for requirement in resolving:
            r = requirement.resolve
            o = await ensure_async(r, self._context_for(r))
            resolving.send(o)
        return await ensure_async(obj, *args, **kw)

    async def extract(self,
                      obj: Callable,
                      requires: RequiresType = None,
                      returns: ReturnsType = None):
        result = await self.call(obj, requires)
        self._process(obj, result, returns)
        return result


class Call(SyncCall):

    async def resolve(self, context):
        result = context.get(self.key, missing)
        if result is missing:
            result = await context.call(self.key)
            if self.cache:
                context.add(result, provides=self.key)
        return result


__all__ = ['Context', 'Call']
