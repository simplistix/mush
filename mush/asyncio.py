import asyncio
from functools import partial
from typing import Callable, Dict, Any

from . import (
    Context as SyncContext, Runner as SyncRunner, ResourceError, ContextError, extract_returns
)
from .declarations import RequirementsDeclaration, ReturnsDeclaration
from .markers import get_mush, AsyncType
from .requirements import Annotation
from .resources import ResourceValue
from .typing import DefaultRequirement


class AsyncFromSyncContext:

    def __init__(self, context, loop):
        self.context: Context = context
        self.loop = loop
        self.add = context.add

    def call(self, obj: Callable, requires: RequirementsDeclaration = None):
        coro = self.context.call(obj, requires)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def extract(
            self,
            obj: Callable,
            requires: RequirementsDeclaration = None,
            returns: ReturnsDeclaration = None
    ):
        coro = self.context.extract(obj, requires, returns)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()


def async_behaviour(callable_):
    to_check = callable_
    if isinstance(callable_, partial):
        to_check = callable_.func
    if asyncio.iscoroutinefunction(to_check):
        return AsyncType.async_
    elif asyncio.iscoroutinefunction(to_check.__call__):
        return AsyncType.async_
    else:
        async_type = get_mush(callable_, 'async', default=None)
        if async_type is None:
            if isinstance(callable_, type):
                return AsyncType.nonblocking
            else:
                return AsyncType.blocking
        else:
            return async_type


class Context(SyncContext):

    def __init__(self, default_requirement: DefaultRequirement = Annotation):
        super().__init__(default_requirement)
        self._sync_context = AsyncFromSyncContext(self, asyncio.get_event_loop())
        self._async_cache = {}

    async def _ensure_async(self, func, *args, **kw):
        behaviour = self._async_cache.get(func)
        if behaviour is None:
            behaviour = async_behaviour(func)
            self._async_cache[func] = behaviour
            
        if behaviour is AsyncType.nonblocking:
            return func(*args, **kw)
        elif behaviour is AsyncType.blocking:
            if kw:
                func = partial(func, **kw)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args)
        else:
            return await func(*args, **kw)

    def _specials(self) -> Dict[type, Any]:
        return {Context: self, SyncContext: self._sync_context}

    async def call(self, obj: Callable, requires: RequirementsDeclaration = None):
        resolving = self._resolve(obj, requires)
        for call in resolving:
            result = await self._ensure_async(call.obj, *call.args, **call.kw)
            if call.send:
                resolving.send(result)
        return result

    async def extract(self,
                      obj: Callable,
                      requires: RequirementsDeclaration = None,
                      returns: ReturnsDeclaration = None):
        result = await self.call(obj, requires)
        returns = extract_returns(obj, returns)
        if returns:
            self.add_by_keys(ResourceValue(result), returns)
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
                    if managed is not None and managed is not result:
                        context.add(managed)
                    # If the context manager swallows an exception,
                    # None should be returned, not the context manager:
                    result = None
                    if context.point is not None:
                        result = await self(context)

        return result


__all__ = ['Context', 'Runner']
