from unittest import TestCase
from mock import Mock

from testfixtures import ShouldRaise, compare

from mush import Context, ContextError

from mush.declarations import (
    nothing, requires, optional, item,
    attr, returns, returns_mapping
)
from mush.resolvers import ValueResolver


class TheType(object):
    def __repr__(self):
        return '<TheType obj>'


class TestContext(TestCase):

    def test_simple(self):
        obj = TheType()
        context = Context()
        context.add(obj)

        compare(context._store, expected={TheType: ValueResolver(obj)})
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
        context.add(obj, provides='my label')

        expected = ("<Context: {\n"
                    "    'my label': <TheType obj>\n"
                    "}>")
        compare(context._store, expected={'my label': ValueResolver(obj)})
        self.assertEqual(repr(context), expected)
        self.assertEqual(str(context), expected)

    def test_explicit_type(self):
        class T2(object): pass
        obj = TheType()
        context = Context()
        context.add(obj, provides=T2)
        compare(context._store, expected={T2: ValueResolver(obj)})
        expected = ("<Context: {\n"
                    "    " + repr(T2) + ": <TheType obj>\n"
                    "}>")
        compare(repr(context), expected)
        compare(str(context), expected)
    
    def test_no_resolver_or_provides(self):
        context = Context()
        with ShouldRaise(ValueError('Cannot add None to context')):
            context.add()
        compare(context._store, expected={})

    def test_resolver_but_no_provides(self):
        context = Context()
        with ShouldRaise(TypeError('Both provides and resolver must be supplied')):
            context.add(resolver=lambda: None)
        compare(context._store, expected={})
    
    def test_resolver(self):
        m = Mock()
        context = Context()
        context.add(provides='foo', resolver=m)
        m.assert_not_called()
        assert context.get('foo') is m.return_value
        m.assert_called_with(context, None)

    def test_resolver_and_resource(self):
        m = Mock()
        context = Context()
        with ShouldRaise(TypeError('resource cannot be supplied when using a resolver')):
            context.add('bar', provides='foo', resolver=m)
        compare(context._store, expected={})

    def test_resolver_with_default(self):
        m = Mock()
        context = Context()
        context.add(provides='foo',
                    resolver=lambda context, default=None: context.get('foo-bar', default))
        assert context.get('foo', default=m) is m

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
        context.add(obj1, provides='my label')
        with ShouldRaise(ContextError("Context already contains 'my label'")):
            context.add(obj2, provides='my label')

    def test_add_none(self):
        context = Context()
        with ShouldRaise(ValueError('Cannot add None to context')):
            context.add(None, type(None))

    def test_add_none_with_type(self):
        context = Context()
        context.add(None, TheType)
        compare(context._store, expected={TheType: ValueResolver(None)})

    def test_call_basic(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.call(foo, nothing)
        compare(result, 'bar')

    def test_call_requires_string(self):
        def foo(obj):
            return obj
        context = Context()
        context.add('bar', 'baz')
        result = context.call(foo, requires('baz'))
        compare(result, 'bar')
        compare({'baz': ValueResolver('bar')}, actual=context._store)

    def test_call_requires_type(self):
        def foo(obj):
            return obj
        context = Context()
        context.add('bar', TheType)
        result = context.call(foo, requires(TheType))
        compare(result, 'bar')
        compare({TheType: ValueResolver('bar')}, actual=context._store)

    def test_call_requires_missing(self):
        def foo(obj): return obj
        context = Context()
        with ShouldRaise(ContextError(
                "No <class 'mush.tests.test_context.TheType'> in context"
        )):
            context.call(foo, requires(TheType))

    def test_call_requires_item_missing(self):
        def foo(obj): return obj
        context = Context()
        context.add({}, TheType)
        with ShouldRaise(ContextError(
                "No TheType['foo'] in context"
        )):
            context.call(foo, requires(item(TheType, 'foo')))

    def test_call_requires_accidental_tuple(self):
        def foo(obj): return obj
        context = Context()
        with ShouldRaise(TypeError(
                "(<class 'mush.tests.test_context.TheType'>, "
                "<class 'mush.tests.test_context.TheType'>) "
                "is not a type or label"
        )):
            context.call(foo, requires((TheType, TheType)))

    def test_call_requires_named_parameter(self):
        def foo(x, y):
            return x, y
        context = Context()
        context.add('foo', TheType)
        context.add('bar', 'baz')
        result = context.call(foo, requires(y='baz', x=TheType))
        compare(result, ('foo', 'bar'))
        compare({TheType: ValueResolver('foo'),
                 'baz': ValueResolver('bar')},
                actual=context._store)

    def test_call_requires_optional_present(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(2, TheType)
        result = context.call(foo, requires(optional(TheType)))
        compare(result, 2)
        compare({TheType: ValueResolver(2)}, actual=context._store)

    def test_call_requires_optional_ContextError(self):
        def foo(x=1):
            return x
        context = Context()
        result = context.call(foo, requires(optional(TheType)))
        compare(result, 1)

    def test_call_requires_optional_override_source_and_default(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(2, provides='x')
        result = context.call(foo, requires(x=Requirement('y', default=3)))
        compare(result, expected=3)

    def test_call_requires_optional_string(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(2, 'foo')
        result = context.call(foo, requires(optional('foo')))
        compare(result, 2)
        compare({'foo': ValueResolver(2)}, actual=context._store)

    def test_call_requires_item(self):
        def foo(x):
            return x
        context = Context()
        context.add(dict(bar='baz'), 'foo')
        result = context.call(foo, requires(item('foo', 'bar')))
        compare(result, 'baz')

    def test_call_requires_attr(self):
        def foo(x):
            return x
        m = Mock()
        context = Context()
        context.add(m, 'foo')
        result = context.call(foo, requires(attr('foo', 'bar')))
        compare(result, m.bar)

    def test_call_requires_item_attr(self):
        def foo(x):
            return x
        m = Mock()
        m.bar= dict(baz='bob')
        context = Context()
        context.add(m, 'foo')
        result = context.call(foo, requires(item(attr('foo', 'bar'), 'baz')))
        compare(result, 'bob')

    def test_call_requires_optional_item_ContextError(self):
        def foo(x=1):
            return x
        context = Context()
        result = context.call(foo, requires(optional(item('foo', 'bar'))))
        compare(result, 1)

    def test_call_requires_optional_item_present(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(dict(bar='baz'), 'foo')
        result = context.call(foo, requires(optional(item('foo', 'bar'))))
        compare(result, 'baz')

    def test_call_requires_item_optional_ContextError(self):
        def foo(x=1):
            return x
        context = Context()
        result = context.call(foo, requires(item(optional('foo'), 'bar')))
        compare(result, 1)

    def test_call_requires_item_optional_present(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(dict(bar='baz'), 'foo')
        result = context.call(foo, requires(item(optional('foo'), 'bar')))
        compare(result, 'baz')

    def test_call_extract_requirements(self):
        def foo(param):
            return param
        context = Context()
        context.add('bar', 'param')
        result = context.call(foo)
        compare(result, 'bar')

    def test_call_extract_no_requirements(self):
        def foo():
            pass
        context = Context()
        result = context.call(foo)
        compare(result, expected=None)

    def test_returns_single(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.extract(foo, nothing, returns(TheType))
        compare(result, 'bar')
        compare({TheType: ValueResolver('bar')}, actual=context._store)

    def test_returns_sequence(self):
        def foo():
            return 1, 2
        context = Context()
        result = context.extract(foo, nothing, returns('foo', 'bar'))
        compare(result, (1, 2))
        compare({'foo': ValueResolver(1), 'bar': ValueResolver(2)},
                actual=context._store)

    def test_returns_mapping(self):
        def foo():
            return {'foo': 1, 'bar': 2}
        context = Context()
        result = context.extract(foo, nothing, returns_mapping())
        compare(result, {'foo': 1, 'bar': 2})
        compare({'foo': ValueResolver(1), 'bar': ValueResolver(2)},
                actual=context._store)

    def test_ignore_return(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.extract(foo, nothing, nothing)
        compare(result, 'bar')
        compare({}, context._store)

    def test_ignore_non_iterable_return(self):
        def foo(): pass
        context = Context()
        result = context.extract(foo, nothing, nothing)
        compare(result, expected=None)
        compare(context._store, expected={})

    def test_context_contains_itself(self):
        context = Context()
        def return_context(context: Context):
            return context
        assert context.call(return_context) is context
        assert context.get(Context) is context

    def test_remove(self):
        context = Context()
        context.add('foo')
        context.remove(str)
        compare(context._store, expected={})

    def test_remove_not_there_strict(self):
        context = Context()
        with ShouldRaise(ContextError("Context does not contain 'foo'")):
            context.remove('foo')
        compare(context._store, expected={})

    def test_remove_not_there_not_strict(self):
        context = Context()
        context.remove('foo', strict=False)
        compare(context._store, expected={})

    def test_get_present(self):
        context = Context()
        context.add('bar', provides='foo')
        compare(context.get('foo'), expected='bar')

    def test_get_missing(self):
        context = Context()
        compare(context.get('foo'), expected=None)
