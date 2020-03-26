import asyncio
from typing import Tuple

import pytest
from testfixtures import compare, ShouldRaise

from mush import Value, requires, returns, Context as SyncContext, blocking, nonblocking
from mush.asyncio import Context
from mush.declarations import RequiresType
from mush.requirements import Requirement, AnyOf, Like
from .helpers import TheType, no_threads, must_run_in_thread
from ..markers import AsyncType


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
    context.add('1', provides='a')
    async def it(a, b='2'):
        return a+b
    with no_threads():
        compare(await context.call(it), expected='12')


@pytest.mark.asyncio
async def test_call_async_requires_context():
    context = Context()
    context.add('bar', provides='baz')
    async def it(context: SyncContext):
        return context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_async_requires_async_context():
    context = Context()
    context.add('bar', provides='baz')
    async def it(context: Context):
        return context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_sync():
    context = Context()
    context.add('foo', provides='baz')
    def it(*, baz):
        return baz+'bar'
    with must_run_in_thread(it):
        compare(await context.call(it), expected='foobar')


@pytest.mark.asyncio
async def test_call_sync_requires_context():
    context = Context()
    context.add('bar', provides='baz')
    def it(context: Context):
        return context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_sync_requires_async_context():
    context = Context()
    context.add('bar', provides='baz')
    def it(context: Context):
        return context.get('baz')
    compare(await context.call(it), expected='bar')


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
async def test_call_cache_requires():
    context = Context()
    def foo(): pass
    await context.call(foo)
    compare(context._requires_cache[foo], expected=RequiresType())


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
    compare(context.get('baz'), expected='bar')


@pytest.mark.asyncio
async def test_extract_async():
    context = Context()
    context.add('foo', provides='bar')
    async def it(context):
        return context.get('bar')+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    compare(context.get('baz'), expected='foobar')


@pytest.mark.asyncio
async def test_extract_sync():
    context = Context()
    context.add('foo', provides='bar')
    def it(context):
        return context.get('bar')+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    compare(context.get('baz'), expected='foobar')


@pytest.mark.asyncio
async def test_extract_minimal():
    o = TheType()
    def foo() -> TheType:
        return o
    context = Context()
    result = await context.extract(foo)
    assert result is o
    compare({TheType: o}, actual=context._store)
    compare(context._requires_cache[foo], expected=RequiresType())
    compare(context._returns_cache[foo], expected=returns(TheType))


@pytest.mark.asyncio
async def test_extract_maximal():
    def foo(*args):
        return args
    context = Context()
    context.add('a')
    result = await context.extract(foo, requires(str), returns(Tuple[str]))
    compare(result, expected=('a',))
    compare({
        str: 'a',
        Tuple[str]: ('a',),
    }, actual=context._store)
    compare(context._requires_cache, expected={})
    compare(context._returns_cache, expected={})


@pytest.mark.asyncio
async def test_value_resolve_does_not_run_in_thread():
    with no_threads():
        context = Context()
        context.add('foo', provides='baz')

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
async def test_custom_requirement_async_resolve():

    class FromRequest(Requirement):
        async def resolve(self, context):
            return (context.get('request'))[self.key]

    def foo(bar: FromRequest('bar')):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')


@pytest.mark.asyncio
async def test_custom_requirement_sync_resolve_get():

    class FromRequest(Requirement):
        def resolve(self, context):
            return context.get('request')[self.key]

    def foo(bar: FromRequest('bar')):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')


@pytest.mark.asyncio
async def test_custom_requirement_sync_resolve_call():

    async def baz(request: dict = Value('request')):
        return request['bar']

    class Syncer(Requirement):
        def resolve(self, context):
            return context.call(self.key)

    def foo(bar: Syncer(baz)):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')


@pytest.mark.asyncio
async def test_custom_requirement_sync_resolve_extract():

    @returns('response')
    async def baz(request: dict = Value('request')):
        return request['bar']

    class Syncer(Requirement):
        def resolve(self, context):
            return context.extract(self.key)

    def foo(bar: Syncer(baz)):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')
    compare(context.get('response'), expected='foo')


@pytest.mark.asyncio
async def test_custom_requirement_sync_resolve_add_remove():

    class Syncer(Requirement):
        def resolve(self, context):
            request = context.get('request')
            context.remove('request')
            context.add(request['bar'], provides='response')
            return request['bar']

    def foo(bar: Syncer('request')):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')
    compare(context.get('request'), expected=None)
    compare(context.get('response'), expected='foo')


@pytest.mark.asyncio
async def test_default_custom_requirement():

    class FromRequest(Requirement):
        async def resolve(self, context):
            return (context.get('request'))[self.key]

    def default_requirement_type(requirement):
        if requirement.__class__ is Requirement:
            requirement.__class__ = FromRequest
        return requirement

    def foo(bar):
        return bar

    context = Context(default_requirement_type)
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')
