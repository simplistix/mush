from testfixtures import compare
from testfixtures.mock import Mock, call
import pytest

from mush.callpoints import CallPoint
from mush.declarations import (
    requires, returns, RequirementsDeclaration, ReturnsDeclaration, update_wrapper
)
from mush.requirements import Value


@pytest.fixture()
def context():
    return Mock()


class TestCallPoints:

    def test_passive_attributes(self):
        # these are managed by Modifiers
        point = CallPoint(Mock())
        compare(point.previous, None)
        compare(point.next, None)
        compare(point.labels, set())

    def test_supplied_explicitly(self, context):
        def foo(a1): pass
        rq = requires('foo')
        rt = returns('bar')
        result = CallPoint(foo, rq, rt)(context)
        compare(result, context.extract.return_value)
        compare(context.extract.mock_calls,
                expected=[call(foo, rq, rt)])

    def test_extract_from_decorations(self, context):
        rq = requires('foo')
        rt = returns('bar')

        @rq
        @rt
        def foo(a1): pass

        result = CallPoint(foo)(context)
        compare(result, context.extract.return_value)
        compare(context.extract.mock_calls,
                expected=[call(foo, None, None)])

    def test_extract_from_decorated_class(self, context):

        rq = requires('foo')
        rt = returns('bar')

        class Wrapper(object):
            def __init__(self, func):
                self.func = func
            def __call__(self):
                return self.func('the ')

        def my_dec(func):
            return update_wrapper(Wrapper(func), func)

        @my_dec
        @rq
        @rt
        def foo(prefix):
            return prefix+'answer'

        context.extract.side_effect = lambda func, rq, rt: (func(), rq, rt)
        result = CallPoint(foo)(context)
        compare(result, expected=('the answer', None, None))

    def test_repr_minimal(self):
        def foo(): pass
        point = CallPoint(foo)
        compare(repr(foo)+" requires() returns('foo')", repr(point))

    def test_repr_maximal(self):
        def foo(a1): pass
        point = CallPoint(foo, requires('foo'), returns('bar'))
        point.labels.add('baz')
        point.labels.add('bob')
        compare(expected=repr(foo)+" requires(Value('foo')) returns('bar') <-- baz, bob",
                actual=repr(point))

    def test_convert_to_requires_and_returns(self):
        def foo(baz): pass
        point = CallPoint(foo, requires='foo', returns='bar')
        # this is deferred until later
        assert isinstance(point.requires, str)
        assert isinstance(point.returns, str)
        compare(repr(foo)+" requires(Value('foo')) returns('bar')",
                repr(point))
