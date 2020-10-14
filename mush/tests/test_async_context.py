import asyncio
from functools import partial
from typing import Tuple

import pytest
from testfixtures import compare, ShouldRaise

from mush import requires, returns, Context as SyncContext, blocking, nonblocking
from mush.asyncio import Context
from mush.requirements import Requirement, AnyOf, Like
from .helpers import TheType, no_threads, must_run_in_thread
from ..markers import AsyncType
from ..resources import ResourceKey, Provider


@pytest.mark.asyncio
async def test_call_is_async():
    context = Context()
    def it():
        return 'bar'
    result = context.call(it)
    assert asyncio.iscoroutine(result)
    with must_run_in_thread(it):
        compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_call_async():
    context = Context()
    context.add('1', identifier='a')
    async def it(a, b='2'):
        return a+b
    with no_threads():
        compare(await context.call(it), expected='12')


@pytest.mark.asyncio
async def test_call_async_callable_object():
    context = Context()

    class AsyncCallable:
        async def __call__(self):
            return 42

    with no_threads():
        compare(await context.call(AsyncCallable()), expected=42)


@pytest.mark.asyncio
async def test_call_partial_around_async():
    context = Context()

    async def it():
        return 42

    with no_threads():
        compare(await context.call(partial(it)), expected=42)


@pytest.mark.asyncio
async def test_call_async_requires_async_context():
    context = Context()
    async def baz():
        return 'bar'
    async def it(context: Context):
        return await context.call(baz) + 'bob'
    compare(await context.call(it), expected='barbob')


@pytest.mark.asyncio
async def test_call_sync():
    context = Context()
    context.add('foo', identifier='baz')
    def it(*, baz):
        return baz+'bar'
    with must_run_in_thread(it):
        compare(await context.call(it), expected='foobar')


@pytest.mark.asyncio
async def test_call_sync_requires_context():
    context = Context()
    # NB: this is intentionally async to test calling async
    # in a sync context:
    async def baz():
        return 'bar'
    # sync method, so needs a sync context:
    def it(context: SyncContext):
        return context.call(baz) + 'bob'
    compare(await context.call(it), expected='barbob')


@pytest.mark.asyncio
async def test_async_provider_async_user():
    o = TheType()
    lookup = {TheType: o}
    async def provider(key: ResourceKey):
        return lookup[key.type]
    context = Context()
    context.add(Provider(provider), provides=TheType)
    async def returner(obj: TheType):
        return obj
    assert await context.call(returner) is o


@pytest.mark.asyncio
async def test_async_provider_sync_user():
    o = TheType()
    lookup = {TheType: o}
    async def provider(key: ResourceKey):
        return lookup[key.type]
    context = Context()
    context.add(Provider(provider), provides=TheType)
    def returner(obj: TheType):
        return obj
    assert await context.call(returner) is o


@pytest.mark.asyncio
async def test_sync_provider_async_user():
    o = TheType()
    lookup = {TheType: o}
    def provider(key: ResourceKey):
        return lookup[key.type]
    context = Context()
    context.add(Provider(provider), provides=TheType)
    async def returner(obj: TheType):
        return obj
    assert await context.call(returner) is o


@pytest.mark.asyncio
async def test_sync_provider_sync_user():
    o = TheType()
    lookup = {TheType: o}
    def provider(key: ResourceKey):
        return lookup[key.type]
    context = Context()
    context.add(Provider(provider), provides=TheType)
    def returner(obj: TheType):
        return obj
    assert await context.call(returner) is o


@pytest.mark.asyncio
async def test_call_class_defaults_to_non_blocking():
    context = Context()
    with no_threads():
        obj = await context.call(TheType)
    assert isinstance(obj, TheType)


@pytest.mark.asyncio
async def test_call_class_explicitly_marked_as_blocking():
    @blocking
    class BlockingType: pass
    context = Context()
    with must_run_in_thread(BlockingType):
        obj = await context.call(BlockingType)
    assert isinstance(obj, BlockingType)


@pytest.mark.asyncio
async def test_call_function_defaults_to_blocking():
    def foo():
        return 42
    context = Context()
    with must_run_in_thread(foo):
        compare(await context.call(foo), expected=42)


@pytest.mark.asyncio
async def test_call_function_explicitly_marked_as_non_blocking():
    @nonblocking
    def foo():
        return 42
    context = Context()
    with no_threads():
        compare(await context.call(foo), expected=42)


@pytest.mark.asyncio
async def test_call_async_function_explicitly_marked_as_non_blocking():
    # sure, I mean, whatever...
    @nonblocking
    async def foo():
        return 42
    context = Context()
    with no_threads():
        compare(await context.call(foo), expected=42)


@pytest.mark.asyncio
async def test_call_async_function_explicitly_marked_as_blocking():
    with ShouldRaise(TypeError('cannot mark an async function as blocking')):
        @blocking
        async def foo(): pass


@pytest.mark.asyncio
async def test_call_caches_asyncness():
    async def foo():
        return 42
    context = Context()
    await context.call(foo)
    compare(context._async_cache[foo], expected=AsyncType.async_)


@pytest.mark.asyncio
async def test_extract_is_async():
    context = Context()
    def it():
        return 'bar'
    result = context.extract(it, requires(), returns('baz'))
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')
    async def returner(baz):
        return baz
    compare(await context.call(returner), expected='bar')


@pytest.mark.asyncio
async def test_extract_async():
    context = Context()
    async def bob():
        return 'foo'
    async def it(context):
        return await context.extract(bob)+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    async def returner(bob):
        return bob
    compare(await context.call(returner), expected='foo')


@pytest.mark.asyncio
async def test_extract_sync():
    context = Context()
    # NB: this is intentionally async to test calling async
    # in a sync context:
    def bob():
        return 'foo'
    def it(context):
        return context.extract(bob)+'bar'
    result = context.extract(it, requires(SyncContext), returns('baz'))
    compare(await result, expected='foobar')
    def returner(bob):
        return bob
    compare(await context.call(returner), expected='foo')


@pytest.mark.asyncio
async def test_extract_minimal():
    o = TheType()
    def foo() -> TheType:
        return o
    context = Context()
    result = await context.extract(foo)
    assert result is o
    async def returner(x: TheType):
        return x
    compare(await context.call(returner), expected=o)


@pytest.mark.asyncio
async def test_extract_maximal():
    def foo(*args):
        return args
    context = Context()
    context.add('a')
    result = await context.extract(foo, requires(str), returns(Tuple[str]))
    compare(result, expected=('a',))
    async def returner(x: Tuple[str]):
        return x
    compare(await context.call(returner), expected=('a',))


@pytest.mark.asyncio
async def test_value_resolve_does_not_run_in_thread():
    with no_threads():
        context = Context()
        context.add('foo', identifier='baz')

        async def it(baz):
            return baz+'bar'

        compare(await context.call(it), expected='foobar')


@pytest.mark.asyncio
async def test_anyof_resolve_does_not_run_in_thread():
    with no_threads():
        context = Context()
        context.add(('foo', ))

        async def bob(x: str = AnyOf(tuple, Tuple[str])):
            return x[0]

        compare(await context.call(bob), expected='foo')


@pytest.mark.asyncio
async def test_like_resolve_does_not_run_in_thread():
    with no_threads():
        o = TheType()
        context = Context()
        context.add(o)

        async def bob(x: str = Like(TheType)):
            return x

        assert await context.call(bob) is o


@pytest.mark.asyncio
async def test_default_custom_requirement():

    class FromRequest(Requirement):
        def __init__(self, name, type_, default):
            self.name = name
            self.type = type_
            super().__init__(keys=[ResourceKey(identifier='request')], default=default)
        def process(self, obj):
            return self.type(obj[self.name])

    def foo(bar: int):
        return bar

    context = Context(FromRequest)
    context.add({'bar': '42'}, identifier='request')
    compare(await context.call(foo), expected=42)
