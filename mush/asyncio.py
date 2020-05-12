import asyncio
from functools import partial
from typing import Callable

from . import (
    Context as SyncContext, Runner as SyncRunner, ResourceError, ContextError
)
from .declarations import RequiresType, ReturnsType
from .extraction import default_requirement_type
from .markers import get_mush, AsyncType
from .typing import RequirementModifier


class AsyncFromSyncContext:

    def __init__(self, context, loop):
        self.context: Context = context
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
        self._async_cache = {}

    async def _ensure_async(self, func, *args, **kw):
        async_type = self._async_cache.get(func)
        if async_type is None:
            to_check = func
            if isinstance(func, partial):
                to_check = func.func
            if asyncio.iscoroutinefunction(to_check):
                async_type = AsyncType.async_
            elif asyncio.iscoroutinefunction(to_check.__call__):
                async_type = AsyncType.async_
            else:
                async_type = get_mush(func, 'async', default=None)
                if async_type is None:
                    if isinstance(func, type):
                        async_type = AsyncType.nonblocking
                    else:
                        async_type = AsyncType.blocking
            self._async_cache[func] = async_type
            
        if async_type is AsyncType.nonblocking:
            return func(*args, **kw)
        elif async_type is AsyncType.blocking:
            if kw:
                func = partial(func, **kw)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args)
        else:
            return await func(*args, **kw)

    def _context_for(self, obj):
        return self if asyncio.iscoroutinefunction(obj) else self._sync_context

    async def call(self, obj: Callable, requires: RequiresType = None):
        args = []
        kw = {}
        resolving = self._resolve(obj, requires, args, kw, self._context_for(obj))
        for requirement in resolving:
            r = requirement.resolve
            o = await self._ensure_async(r, self._context_for(r))
            resolving.send(o)
        return await self._ensure_async(obj, *args, **kw)

    async def extract(self,
                      obj: Callable,
                      requires: RequiresType = None,
                      returns: ReturnsType = None):
        result = await self.call(obj, requires)
        self._process(obj, result, returns)
        return result


class SyncContextManagerWrapper:

    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.loop = asyncio.get_event_loop()

    async def __aenter__(self):
        return await self.loop.run_in_executor(None, self.sync_manager.__enter__)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.loop.run_in_executor(None, self.sync_manager.__exit__,
                                               exc_type, exc_val, exc_tb)


class Runner(SyncRunner):

    async def __call__(self, context: Context = None):
        if context is None:
            context = Context()
        if context.point is None:
            context.point = self.start

        result = None

        while context.point:

            point = context.point
            context.point = point.next

            try:
                result = manager = await point(context)
            except ResourceError as e:
                raise ContextError(str(e), point, context)

            if getattr(result, '__enter__', None):
                manager = SyncContextManagerWrapper(result)

            if getattr(manager, '__aenter__', None):
                async with manager as managed:
                    if managed is not None:
                        context.add(managed)
                    # If the context manager swallows an exception,
                    # None should be returned, not the context manager:
                    result = None
                    if context.point is not None:
                        result = await self(context)

        return result


__all__ = ['Context', 'Runner']
