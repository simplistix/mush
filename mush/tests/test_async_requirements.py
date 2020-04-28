import pytest
from testfixtures import compare

from mush.asyncio import Context, Call


class TestCall:

    @pytest.mark.asyncio
    async def test_resolve(self):
        context = Context()

        called = []

        async def foo(bar: str):
            called.append(1)
            return bar+'b'

        async def bob(x: str = Call(foo)):
            return x+'c'

        context.add('a', provides='bar')

        compare(await context.call(bob), expected='abc')
        compare(await context.call(bob), expected='abc')
        compare(called, expected=[1])
        compare(context.get(foo), expected='ab')

    @pytest.mark.asyncio
    async def test_resolve_without_caching(self):
        context = Context()

        called = []

        def foo(bar: str):
            called.append(1)
            return bar+'b'

        def bob(x: str = Call(foo, cache=False)):
            return x+'c'

        context.add('a', provides='bar')

        compare(await context.call(bob), expected='abc')
        compare(await context.call(bob), expected='abc')
        compare(called, expected=[1, 1])
        compare(context.get(foo, default=None), expected=None)

    @pytest.mark.asyncio
    async def test_parts_of_a_call(self):
        context = Context()

        async def foo():
            return {'a': 'b'}

        async def bob(x: str = Call(foo)['a']):
            return x+'c'

        compare(await context.call(bob), expected='bc')
