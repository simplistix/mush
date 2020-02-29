import asyncio
from typing import Tuple

import pytest

from mush import Context, requires, returns
from mush.asyncio import Context
from mush.context import ResolvableValue
from mush.declarations import Requirement, RequiresType
from testfixtures import compare

from mush.tests.test_context import TheType


@pytest.mark.asyncio
async def test_get_is_async():
    context = Context()
    result = context.get('foo', default='bar')
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_get_async_resolver():
    async def resolver(*args):
        return 'bar'
    context = Context()
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_get_async_resolver_calls_back_into_async():
    async def resolver(context, default):
        return await context.get('baz')
    context = Context()
    context.add('bar', provides='baz')
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_get_sync_resolver():
    def resolver(*args):
        return 'bar'
    context = Context()
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_get_sync_resolver_calls_back_into_async():
    def resolver(context, default):
        return context.get('baz')
    context = Context()
    context.add('bar', provides='baz')
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_call_is_async():
    context = Context()
    def it():
        return 'bar'
    result = context.call(it)
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_call_async():
    context = Context()
    context.add('1', provides='a')
    async def it(a, b='2'):
        return a+b
    compare(await context.call(it), expected='12')


@pytest.mark.asyncio
async def test_call_async_requires_context():
    context = Context()
    context.add('bar', provides='baz')
    async def it(context: Context):
        return await context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_async_requires_async_context():
    context = Context()
    context.add('bar', provides='baz')
    async def it(context: Context):
        return await context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_sync():
    context = Context()
    context.add('foo', provides='baz')
    def it(*, baz):
        return baz+'bar'
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
async def test_call_cache_requires():
    context = Context()
    def foo(): pass
    await context.call(foo)
    compare(context._requires_cache[foo], expected=RequiresType())


@pytest.mark.asyncio
async def test_extract_is_async():
    context = Context()
    def it():
        return 'bar'
    result = context.extract(it, requires(), returns('baz'))
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')
    compare(await context.get('baz'), expected='bar')


@pytest.mark.asyncio
async def test_extract_async():
    context = Context()
    context.add('foo', provides='bar')
    async def it(context):
        return await context.get('bar')+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    compare(await context.get('baz'), expected='foobar')


@pytest.mark.asyncio
async def test_extract_sync():
    context = Context()
    context.add('foo', provides='bar')
    def it(context):
        return context.get('bar')+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    compare(await context.get('baz'), expected='foobar')


@pytest.mark.asyncio
async def test_extract_minimal():
    o = TheType()
    def foo() -> TheType:
        return o
    context = Context()
    result = await context.extract(foo)
    assert result is o
    compare({TheType: ResolvableValue(o)}, actual=context._store)
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
        str: ResolvableValue('a'),
        Tuple[str]: ResolvableValue(('a',)),
    }, actual=context._store)
    compare(context._requires_cache, expected={})
    compare(context._returns_cache, expected={})


@pytest.mark.asyncio
async def test_custom_requirement_async_resolve():

    class FromRequest(Requirement):
        async def resolve(self, context):
            return (await context.get('request'))[self.key]

    def foo(bar: FromRequest('bar')):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')


@pytest.mark.asyncio
async def test_custom_requirement_sync_resolve():

    class FromRequest(Requirement):
        def resolve(self, context):
            return context.get('request')[self.key]

    def foo(bar: FromRequest('bar')):
        return bar

    context = Context()
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')


@pytest.mark.asyncio
async def test_default_custom_requirement():


    class FromRequest(Requirement):
        async def resolve(self, context):
            return (await context.get('request'))[self.key]

    def foo(bar):
        return bar

    context = Context(FromRequest)
    context.add({'bar': 'foo'}, provides='request')
    compare(await context.call(foo), expected='foo')
