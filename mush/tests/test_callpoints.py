from functools import update_wrapper
from unittest import TestCase

from mock import Mock
from testfixtures import compare

from mush.callpoints import CallPoint
from mush.declarations import requires, returns, RequiresType, Requirement
from mush.extraction import update_wrapper


class TestCallPoints(TestCase):

    def setUp(self):
        self.context = Mock()

    def test_passive_attributes(self):
        # these are managed by Modifiers
        point = CallPoint(self.context)
        compare(point.previous, None)
        compare(point.next, None)
        compare(point.labels, set())

    def test_supplied_explicitly(self):
        def foo(a1): pass
        rq = requires('foo')
        rt = returns('bar')
        result = CallPoint(foo, rq, rt)(self.context)
        compare(result, self.context.extract.return_value)
        compare(tuple(self.context.extract.mock_calls[0].args),
                expected=(foo,
                          RequiresType((Requirement('foo', name='a1'),)),
                          rt))

    def test_extract_from_decorations(self):
        rq = requires('foo')
        rt = returns('bar')

        @rq
        @rt
        def foo(a1): pass

        result = CallPoint(foo)(self.context)
        compare(result, self.context.extract.return_value)
        compare(tuple(self.context.extract.mock_calls[0].args),
                expected=(foo,
                          RequiresType((Requirement('foo', name='a1'),)),
                          returns('bar')))

    def test_extract_from_decorated_class(self):

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

        self.context.extract.side_effect = lambda func, rq, rt: (func(), rq, rt)
        result = CallPoint(foo)(self.context)
        compare(result, expected=('the answer',
                                  RequiresType((Requirement('foo', name='prefix'),)),
                                  rt))

    def test_explicit_trumps_decorators(self):
        @requires('foo')
        @returns('bar')
        def foo(a1): pass

        result = CallPoint(foo, requires('baz'), returns('bob'))(self.context)
        compare(result, self.context.extract.return_value)
        compare(tuple(self.context.extract.mock_calls[0].args),
                expected=(foo,
                          RequiresType((Requirement('baz', name='a1'),)),
                          returns('bob')))

    def test_repr_minimal(self):
        def foo(): pass
        point = CallPoint(foo)
        compare(repr(foo)+" requires() returns_result_type()", repr(point))

    def test_repr_maximal(self):
        def foo(a1): pass
        point = CallPoint(foo, requires('foo'), returns('bar'))
        point.labels.add('baz')
        point.labels.add('bob')
        compare(repr(foo)+" requires('foo') returns('bar') <-- baz, bob",
                repr(point))

    def test_convert_to_requires_and_returns(self):
        def foo(baz): pass
        point = CallPoint(foo, requires='foo', returns='bar')
        self.assertTrue(isinstance(point.requires, RequiresType))
        self.assertTrue(isinstance(point.returns, returns))
        compare(repr(foo)+" requires('foo') returns('bar')",
                repr(point))

    def test_convert_to_requires_and_returns_tuple(self):
        def foo(a1, a2): pass
        point = CallPoint(foo,
                          requires=('foo', 'bar'),
                          returns=('baz', 'bob'))
        self.assertTrue(isinstance(point.requires, RequiresType))
        self.assertTrue(isinstance(point.returns, returns))
        compare(repr(foo)+" requires('foo', 'bar') returns('baz', 'bob')",
                repr(point))

    def test_convert_to_requires_and_returns_list(self):
        def foo(a1, a2): pass
        point = CallPoint(foo,
                          requires=['foo', 'bar'],
                          returns=['baz', 'bob'])
        self.assertTrue(isinstance(point.requires, RequiresType))
        self.assertTrue(isinstance(point.returns, returns))
        compare(repr(foo)+" requires('foo', 'bar') returns('baz', 'bob')",
                repr(point))
