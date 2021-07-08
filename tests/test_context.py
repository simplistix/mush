from testfixtures import compare

from mush.context import Context


class TestCall:

    def test_no_params(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.call(foo)
        compare(result, 'bar')
