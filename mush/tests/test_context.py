from unittest import TestCase
from mock import Mock

from testfixtures import ShouldRaise, compare

from mush.context import Context, ContextError

from mush.declarations import (
    nothing, result_type, requires, optional, item,
    attr, returns, returns_mapping
)


class TheType(object):
    def __repr__(self):
        return '<TheType obj>'


class TestContext(TestCase):

    def test_simple(self):
        obj = TheType()
        context = Context()
        context.add(obj, TheType)

        self.assertTrue(context[TheType] is obj)
        expected = (
            "<Context: {\n"
            "    <class 'mush.tests.test_context.TheType'>: <TheType obj>\n"
            "}>"
        )
        self.assertEqual(repr(context), expected)
        self.assertEqual(str(context), expected)

    def test_type_as_string(self):
        obj = TheType()
        context = Context()
        context.add(obj, type='my label')

        expected = ("<Context: {\n"
                    "    'my label': <TheType obj>\n"
                    "}>")
        self.assertTrue(context['my label'] is obj)
        self.assertEqual(repr(context), expected)
        self.assertEqual(str(context), expected)

    def test_explicit_type(self):
        class T2(object): pass
        obj = TheType()
        context = Context()
        context.add(obj, T2)
        self.assertTrue(context[T2] is obj)
        expected = ("<Context: {\n"
                    "    " + repr(T2) + ": <TheType obj>\n"
                    "}>")
        compare(repr(context), expected)
        compare(str(context), expected)

    def test_clash(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, TheType)
        with ShouldRaise(ContextError('Context already contains '+repr(TheType))):
            context.add(obj2, TheType)

    def test_clash_string_type(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, type='my label')
        with ShouldRaise(ContextError("Context already contains 'my label'")):
            context.add(obj2, type='my label')

    def test_add_none(self):
        context = Context()
        with ShouldRaise(ValueError('Cannot add None to context')):
            context.add(None, None.__class__)

    def test_add_none_with_type(self):
        context = Context()
        context.add(None, TheType)
        self.assertTrue(context[TheType] is None)

    def test_call_basic(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.call(foo, nothing, result_type)
        compare(result, 'bar')
        compare({str: 'bar'}, context)

    def test_call_requires_string(self):
        def foo(obj):
            return obj
        context = Context()
        context.add('bar', 'baz')
        result = context.call(foo, requires('baz'), result_type)
        compare(result, 'bar')
        compare({'baz': 'bar', str: 'bar'}, context)

    def test_call_requires_type(self):
        def foo(obj):
            return obj
        context = Context()
        context.add('bar', TheType)
        result = context.call(foo, requires(TheType), result_type)
        compare(result, 'bar')
        compare({TheType: 'bar', str: 'bar'}, context)

    def test_call_requires_missing(self):
        def foo(obj):
            return obj
        context = Context()
        with ShouldRaise(ContextError(
                "No <class 'mush.tests.test_context.TheType'> in context"
        )):
            context.call(foo, requires(TheType), result_type)

    def test_call_requires_item_missing(self):
        def foo(obj):
            return obj
        context = Context()
        context.add({}, TheType)
        with ShouldRaise(ContextError(
                "No TheType['foo'] in context"
        )):
            context.call(foo, requires(item(TheType, 'foo')), result_type)

    def test_call_requires_accidental_tuple(self):
        def foo(obj):
            return obj
        context = Context()
        with ShouldRaise(TypeError(
                "(<class 'mush.tests.test_context.TheType'>, "
                "<class 'mush.tests.test_context.TheType'>) "
                "is not a type or label"
        )):
            context.call(foo, requires((TheType, TheType)), result_type)

    def test_call_requires_named_parameter(self):
        def foo(x, y):
            return x, y
        context = Context()
        context.add('foo', TheType)
        context.add('bar', 'baz')
        result = context.call(foo,
                              requires(y='baz', x=TheType),
                              result_type)
        compare(result, ('foo', 'bar'))
        compare({TheType: 'foo',
                 'baz': 'bar',
                 tuple: ('foo', 'bar')}, context)

    def test_call_requires_optional_present(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(2, TheType)
        result = context.call(foo,
                              requires(optional(TheType)),
                              result_type)
        compare(result, 2)
        compare({TheType: 2, int: 2}, context)

    def test_call_requires_optional_ContextError(self):
        def foo(x=1):
            return x
        context = Context()
        result = context.call(foo,
                              requires(optional(TheType)),
                              result_type)
        compare(result, 1)
        compare({int: 1}, context)

    def test_call_requires_optional_string(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(2, 'foo')
        result = context.call(foo,
                              requires(optional('foo')),
                              result_type)
        compare(result, 2)
        compare({'foo': 2, int: 2}, context)

    def test_call_requires_item(self):
        def foo(x):
            return x
        context = Context()
        context.add(dict(bar='baz'), 'foo')
        result = context.call(foo,
                              requires(item('foo', 'bar')),
                              result_type)
        compare(result, 'baz')

    def test_call_requires_attr(self):
        def foo(x):
            return x
        m = Mock()
        context = Context()
        context.add(m, 'foo')
        result = context.call(foo,
                              requires(attr('foo', 'bar')),
                              result_type)
        compare(result, m.bar)

    def test_call_requires_item_attr(self):
        def foo(x):
            return x
        m = Mock()
        m.bar= dict(baz='bob')
        context = Context()
        context.add(m, 'foo')
        result = context.call(foo,
                              requires(item(attr('foo', 'bar'), 'baz')),
                              result_type)
        compare(result, 'bob')

    def test_call_requires_optional_item_ContextError(self):
        def foo(x=1):
            return x
        context = Context()
        result = context.call(foo,
                              requires(optional(item('foo', 'bar'))),
                              result_type)
        compare(result, 1)

    def test_call_requires_optional_item_present(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(dict(bar='baz'), 'foo')
        result = context.call(foo,
                              requires(optional(item('foo', 'bar'))),
                              result_type)
        compare(result, 'baz')

    def test_call_requires_item_optional_ContextError(self):
        def foo(x=1):
            return x
        context = Context()
        result = context.call(foo,
                              requires(item(optional('foo'), 'bar')),
                              result_type)
        compare(result, 1)

    def test_call_requires_item_optional_present(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(dict(bar='baz'), 'foo')
        result = context.call(foo,
                              requires(item(optional('foo'), 'bar')),
                              result_type)
        compare(result, 'baz')

    def test_returns_single(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.call(foo, nothing, returns(TheType))
        compare(result, 'bar')
        compare({TheType: 'bar'}, context)

    def test_returns_sequence(self):
        def foo():
            return 1, 2
        context = Context()
        result = context.call(foo, nothing, returns('foo', 'bar'))
        compare(result, (1, 2))
        compare({'foo': 1, 'bar': 2}, context)

    def test_returns_mapping(self):
        def foo():
            return {'foo': 1, 'bar': 2}
        context = Context()
        result = context.call(foo, nothing, returns_mapping())
        compare(result, {'foo': 1, 'bar': 2})
        compare({'foo': 1, 'bar': 2}, context)

    def test_ignore_return(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.call(foo, nothing, returns())
        compare(result, 'bar')
        compare({}, context)


