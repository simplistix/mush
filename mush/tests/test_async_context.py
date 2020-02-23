import asyncio
import pytest

from mush import AsyncContext, Context, requires, returns
from testfixtures import compare


@pytest.mark.asyncio
async def test_get_is_async():
    context = AsyncContext()
    result = context.get('foo', default='bar')
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_get_async_resolver():
    async def resolver(*args):
        return 'bar'
    context = AsyncContext()
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_get_async_resolver_calls_back_into_async():
    async def resolver(context, default):
        return await context.get('baz')
    context = AsyncContext()
    context.add('bar', provides='baz')
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_get_sync_resolver():
    def resolver(*args):
        return 'bar'
    context = AsyncContext()
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_get_sync_resolver_calls_back_into_async():
    def resolver(context, default):
        return context.get('baz')
    context = AsyncContext()
    context.add('bar', provides='baz')
    context.add(provides='foo', resolver=resolver)
    compare(await context.get('foo'), expected='bar')


@pytest.mark.asyncio
async def test_call_is_async():
    context = AsyncContext()
    def it():
        return 'bar'
    result = context.call(it)
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_call_async():
    context = AsyncContext()
    context.add('1', provides='a')
    async def it(a, b='2'):
        return a+b
    compare(await context.call(it), expected='12')


@pytest.mark.asyncio
async def test_call_async_requires_context():
    context = AsyncContext()
    context.add('bar', provides='baz')
    async def it(context: Context):
        return await context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_async_requires_async_context():
    context = AsyncContext()
    context.add('bar', provides='baz')
    async def it(context: AsyncContext):
        return await context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_sync():
    context = AsyncContext()
    context.add('foo', provides='baz')
    def it(*, baz):
        return baz+'bar'
    compare(await context.call(it), expected='foobar')


@pytest.mark.asyncio
async def test_call_sync_requires_context():
    context = AsyncContext()
    context.add('bar', provides='baz')
    def it(context: Context):
        return context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_call_sync_requires_async_context():
    context = AsyncContext()
    context.add('bar', provides='baz')
    def it(context: AsyncContext):
        return context.get('baz')
    compare(await context.call(it), expected='bar')


@pytest.mark.asyncio
async def test_extract_is_async():
    context = AsyncContext()
    def it():
        return 'bar'
    result = context.extract(it, requires(), returns('baz'))
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')
    compare(await context.get('baz'), expected='bar')


@pytest.mark.asyncio
async def test_extract_async():
    context = AsyncContext()
    context.add('foo', provides='bar')
    async def it(context):
        return await context.get('bar')+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    compare(await context.get('baz'), expected='foobar')


@pytest.mark.asyncio
async def test_extract_sync():
    context = AsyncContext()
    context.add('foo', provides='bar')
    def it(context):
        return context.get('bar')+'bar'
    result = context.extract(it, requires(Context), returns('baz'))
    compare(await result, expected='foobar')
    compare(await context.get('baz'), expected='foobar')
