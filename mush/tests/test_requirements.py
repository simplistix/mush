from testfixtures import compare

from mush import Context, Call


class TestCall:

    def test_resolve(self):
        context = Context()

        called = []

        def foo(bar: str):
            called.append(1)
            return bar+'b'

        def bob(x: str = Call(foo)):
            return x+'c'

        context.add('a', provides='bar')

        compare(context.call(bob), expected='abc')
        compare(context.call(bob), expected='abc')
        compare(called, expected=[1])
        compare(context.get(foo), expected='ab')

    def test_resolve_without_caching(self):
        context = Context()

        called = []

        def foo(bar: str):
            called.append(1)
            return bar+'b'

        def bob(x: str = Call(foo, cache=False)):
            return x+'c'

        context.add('a', provides='bar')

        compare(context.call(bob), expected='abc')
        compare(context.call(bob), expected='abc')
        compare(called, expected=[1, 1])
        compare(context.get(foo), expected=None)

    def test_parts_of_a_call(self):
        context = Context()

        def foo():
            return {'a': 'b'}

        def bob(x: str = Call(foo)['a']):
            return x+'c'

        compare(context.call(bob), expected='bc')
