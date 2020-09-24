from testfixtures import compare

from mush import Context


class TestCall:

    def test_positional_only(self):
        def foo(x:int, /):
            return x

        context = Context()
        context.add(2)
        result = context.call(foo)
        compare(result, expected=2)

    def test_positional_only_with_default(self):
        def foo(x:int = 1, /):
            return x

        context = Context()
        result = context.call(foo)
        compare(result, expected=1)
