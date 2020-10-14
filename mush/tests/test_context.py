from functools import partial
from typing import NewType, Mapping, Any, Tuple

import pytest
from testfixtures import ShouldRaise, compare
from testfixtures.mock import Mock

from mush import Context, Requirement, Value, requires, missing
from mush.context import ResourceError
from .helpers import TheType, Type1, Type2
from ..compat import PY_37_PLUS
from ..declarations import ignore_return
from ..resources import ResourceValue, Provider, ResourceKey


class TestAdd:

    def test_by_inferred_type(self):
        obj = TheType()
        context = Context()
        context.add(obj)

        compare(context._store, expected={(TheType, None): ResourceValue(obj)})
        expected = (
            "<Context: {\n"
            "    TheType: <TheType obj>\n"
            "}>"
        )
        compare(expected, actual=repr(context))
        compare(expected, actual=str(context))

    def test_by_identifier(self):
        obj = TheType()
        context = Context()
        context.add(obj, identifier='my label')

        compare(context._store, expected={
            (TheType, 'my label'): ResourceValue(obj),
            (None, 'my label'): ResourceValue(obj),
        })
        expected = ("<Context: {\n"
                    "    'my label': <TheType obj>\n"
                    "    TheType, 'my label': <TheType obj>\n"
                    "}>")
        compare(expected, actual=repr(context))
        compare(expected, actual=str(context))

    def test_by_identifier_only(self):
        obj = TheType()
        context = Context()
        context.add(obj, provides=None, identifier='my label')

        compare(context._store, expected={(None, 'my label'): ResourceValue(obj)})
        expected = ("<Context: {\n"
                    "    'my label': <TheType obj>\n"
                    "}>")
        compare(expected, actual=repr(context))
        compare(expected, actual=str(context))

    def test_explicit_type(self):
        obj = TheType()
        context = Context()
        context.add(obj, provides=Type2)
        compare(context._store, expected={(Type2, None): ResourceValue(obj)})
        expected = ("<Context: {\n"
                    "    Type2: <TheType obj>\n"
                    "}>")
        compare(expected, actual=repr(context))
        compare(expected, actual=str(context))

    def test_clash_just_type(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, TheType)
        with ShouldRaise(ResourceError(f'Context already contains TheType')):
            context.add(obj2, TheType)

    def test_clash_just_identifier(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, provides=None, identifier='my label')
        with ShouldRaise(ResourceError("Context already contains 'my label'")):
            context.add(obj2, provides=None, identifier='my label')

    def test_clash_identifier_only_with_identifier_plus_type(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, provides=None, identifier='my label')
        with ShouldRaise(ResourceError("Context already contains 'my label'")):
            context.add(obj2, identifier='my label')

    def test_clash_identifier_plus_type_with_identifier_only(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, identifier='my label')
        with ShouldRaise(ResourceError("Context already contains 'my label'")):
            context.add(obj2, provides=None, identifier='my label')


class TestCall:

    def test_no_params(self):
        def foo():
            return 'bar'
        context = Context()
        result = context.call(foo)
        compare(result, 'bar')

    def test_type_from_annotation(self):
        def foo(baz: str):
            return baz
        context = Context()
        context.add('bar')
        result = context.call(foo)
        compare(result, expected='bar')

    def test_identifier_from_annotation(self):
        def foo(baz: str):
            return baz
        context = Context()
        context.add('bar', provides=str)
        context.add('bob', identifier='baz')
        result = context.call(foo)
        compare(result, expected='bob')

    def test_by_identifier_only(self):
        def foo(param):
            return param

        context = Context()
        context.add('bar', identifier='param')
        result = context.call(foo)
        compare(result, 'bar')

    def test_requires_missing(self):
        def foo(obj: TheType): return obj
        context = Context()
        with ShouldRaise(ResourceError(
            "obj: TheType could not be satisfied"
        )):
            context.call(foo)

    def test_optional_type_present(self):
        def foo(x: TheType = 1):
            return x
        context = Context()
        context.add(2, TheType)
        result = context.call(foo)
        compare(result, 2)

    def test_optional_type_missing(self):
        def foo(x: TheType = 1):
            return x
        context = Context()
        result = context.call(foo)
        compare(result, 1)

    def test_optional_identifier_present(self):
        def foo(x=1):
            return x

        context = Context()
        context.add(2, identifier='x')
        result = context.call(foo)
        compare(result, 2)

    def test_optional_identifier_missing(self):
        def foo(x=1):
            return x

        context = Context()
        context.add(2)
        result = context.call(foo)
        compare(result, 1)

    def test_requires_context(self):
        context = Context()

        def return_context(context_: Context):
            return context_

        assert context.call(return_context) is context

    def test_base_class_should_not_match(self):
        def foo(obj: TheType): return obj
        context = Context()
        context.add(object())
        with ShouldRaise(ResourceError(
            "obj: TheType could not be satisfied"
        )):
            context.call(foo)

    def test_requires_typing(self):
        Request = NewType('Request', dict)
        context = Context()
        request = {}
        context.add(request, provides=Request)

        def returner(request_: Request):
            return request_

        assert context.call(returner) is request

    def test_requires_typing_missing_typing(self):
        context = Context()

        def returner(request_: Mapping[str, Any]):
            pass

        if PY_37_PLUS:
            expected = "request_: typing.Mapping[str, typing.Any] could not be satisfied"
        else:
            expected = "request_: Mapping could not be satisfied"

        with ShouldRaise(ResourceError(expected)):
            context.call(returner)

    def test_requires_typing_missing_new_type(self):
        Request = NewType('Request', dict)
        context = Context()

        def returner(request_: Request):
            pass

        with ShouldRaise(ResourceError(
                "request_: Request could not be satisfied"
        )):
            context.call(returner)

    def test_requires_requirement(self):
        context = Context()

        def foo(requirement: Requirement): pass

        with ShouldRaise(ResourceError(
                "requirement: Requirement could not be satisfied"
        )):
            context.call(foo)

    def test_keyword_only(self):
        def foo(*, x: int):
            return x

        context = Context()
        context.add(2)
        result = context.call(foo)
        compare(result, expected=2)

    def test_call_requires_string(self):
        def foo(obj):
            return obj
        context = Context()
        context.add('bar', identifier='baz')
        result = context.call(foo, requires('baz'))
        compare(result, expected='bar')

    def test_call_requires_type(self):
        def foo(obj):
            return obj
        context = Context()
        context.add('bar', TheType)
        result = context.call(foo, requires(TheType))
        compare(result, 'bar')

    def test_call_requires_optional_override_source_and_default(self):
        def foo(x=1):
            return x
        context = Context()
        context.add(2, provides='x')
        result = context.call(foo, requires(x=Value('y', default=3)))
        compare(result, expected=3)

    def test_kw_parameter(self):
        def foo(x, y):
            return x, y
        context = Context()
        context.add('foo', TheType)
        context.add('bar', identifier='baz')
        result = context.call(foo, requires(y='baz', x=TheType))
        compare(result, expected=('foo', 'bar'))


class TestOps:

    def test_call_requires_item(self):
        def foo(x: str = Value(identifier='foo')['bar']):
            return x
        context = Context()
        context.add(dict(bar='baz'), identifier='foo')
        result = context.call(foo)
        compare(result, expected='baz')

    def test_call_requires_item_missing(self):
        def foo(obj: str = Value(dict)['foo']): pass
        context = Context()
        context.add({})
        with ShouldRaise(ResourceError(
            "Value(dict)['foo'] could not be satisfied",
        )):
            context.call(foo)

    def test_call_requires_optional_item_missing(self):
        def foo(x: str = Value('foo', default=1)['bar']):
            return x
        context = Context()
        result = context.call(foo)
        compare(result, expected=1)

    def test_call_requires_optional_item_present(self):
        def foo(x: str = Value('foo', default=1)['bar']):
            return x
        context = Context()
        context.add(dict(bar='baz'), identifier='foo')
        result = context.call(foo)
        compare(result, expected='baz')

    def test_call_requires_attr(self):
        @requires(Value('foo').bar)
        def foo(x):
            return x
        m = Mock()
        context = Context()
        context.add(m, identifier='foo')
        result = context.call(foo)
        compare(result, m.bar)

    def test_call_requires_attr_missing(self):
        @requires(Value('foo').bar)
        def foo(x):
            pass
        o = object()
        context = Context()
        context.add(o, identifier='foo')
        with ShouldRaise(ResourceError(
            "Value('foo').bar could not be satisfied",
        )):
            context.call(foo)

    def test_call_requires_optional_attr_missing(self):
        @requires(Value('foo', default=1).bar)
        def foo(x):
            return x
        o = object()
        context = Context()
        context.add(o, identifier='foo')
        result = context.call(foo)
        compare(result,  expected=1)

    def test_call_requires_optional_attr_present(self):
        @requires(Value('foo', default=1).bar)
        def foo(x):
            return x
        m = Mock()
        context = Context()
        context.add(m, identifier='foo')
        result = context.call(foo)
        compare(result, expected=m.bar)

    def test_call_requires_item_attr(self):
        @requires(Value('foo').bar['baz'])
        def foo(x):
            return x
        m = Mock()
        m.bar = dict(baz='bob')
        context = Context()
        context.add(m, identifier='foo')
        result = context.call(foo)
        compare(result,  expected='bob')


class TestExtract:

    def test_extract_minimal(self):
        o = TheType()
        def foo():
            return o
        context = Context()
        result = context.extract(foo)
        assert result is o
        compare({ResourceKey(identifier='foo'): ResourceValue(o)}, actual=context._store)

    def test_extract_maximal(self):
        def foo(o: str) -> Tuple[str, ...]:
            return o, o
        context = Context()
        context.add('a')
        result = context.extract(foo)
        compare(result, expected=('a', 'a'))
        compare({
            ResourceKey(str): ResourceValue('a'),
            ResourceKey(identifier='foo'): ResourceValue(result),
            ResourceKey(Tuple[str, ...], 'foo'): ResourceValue(result),
            ResourceKey(Tuple[str, ...]): ResourceValue(result),
        }, actual=context._store)

    def test_ignore_return(self):
        @ignore_return
        def foo():
            return 'bar'
        context = Context()
        result = context.extract(foo)
        compare(result, 'bar')
        compare({}, context._store)

    def test_returns_none(self):
        def foo(): pass
        context = Context()
        result = context.extract(foo)
        compare(result, expected=None)
        compare(context._store, expected={
            ResourceKey(identifier='foo'): ResourceValue(None),
        })


class TestProviders:

    def test_cached(self):
        items = []

        def provider():
            items.append(1)
            return sum(items)

        context = Context()
        context.add(Provider(provider), provides=int)

        def returner(obj: int):
            return obj

        compare(context.call(returner), expected=1)
        compare(context.call(returner), expected=1)

    def test_not_cached(self):
        items = []

        def provider():
            items.append(1)
            return sum(items)

        context = Context()
        context.add(Provider(provider, cache=False), provides=int)

        def returner(obj: int):
            return obj

        compare(context.call(returner), expected=1)
        compare(context.call(returner), expected=2)

    def test_needs_resources(self):
        def provider(start: int):
            return start*2

        context = Context()
        context.add(Provider(provider), provides=int)
        context.add(4, identifier='start')

        def returner(obj: int):
            return obj

        compare(context.call(returner), expected=8)

    def test_needs_requirement(self):
        def provider(requirement: Requirement):
            return requirement.keys[0].identifier

        context = Context()
        context.add(Provider(provider), provides=str)

        def returner(obj: str):
            return obj

        compare(context.call(returner), expected='obj')

    def test_needs_resource_key(self):
        def provider(key: ResourceKey):
            return key.type, key.identifier

        context = Context()
        context.add(Provider(provider), provides=tuple)

        def returner(obj: tuple):
            return obj

        compare(context.call(returner), expected=(tuple, 'obj'))

    def test_provides_subclasses(self):
        class Base: pass

        class TheType(Base): pass

        def provider(requirement: Requirement):
            return requirement.keys[0].type()

        def foo(bar: TheType):
            return bar

        context = Context()
        context.add(Provider(provider, provides_subclasses=True), provides=Base)

        assert isinstance(context.call(foo), TheType)

    def test_provides_subclasses_caching(self):
        class Base: pass
        class Type1(Base): pass
        class Type2(Base): pass

        t1 = Type1()
        t2 = Type2()
        instances = {Type1: t1, Type2: t2}

        def provider(requirement: Requirement):
            # .pop so each instance can only be obtained once!
            return instances.pop(requirement.keys[0].type)

        def foo(bar):
            return bar

        context = Context()
        context.add(Provider(provider, cache=True, provides_subclasses=True), provides=Base)

        assert context.call(foo, requires=Type1) is t1
        # cached:
        assert context.call(foo, requires=Type1) is t1
        assert context.call(foo, requires=Type2) is t2
        assert context.call(foo, requires=Type2) is t2

    def test_does_not_provide_subclasses(self):
        def foo(obj: TheType): pass

        context = Context()
        context.add(Provider(lambda: None), provides=object)

        with ShouldRaise(ResourceError(
            "obj: TheType could not be satisfied"
        )):
            context.call(foo)

    def test_multiple_providers_using_requirement(self):
        def provider(requirement: Requirement):
            return requirement.keys[0].type()

        def foo(t1: Type1, t2: Type2):
            return t1, t2

        context = Context()
        context.add(Provider(provider), provides=Type1)
        context.add(Provider(provider), provides=Type2)

        t1, t2 = context.call(foo)
        assert isinstance(t1, Type1)
        assert isinstance(t2, Type2)

    def test_nested_providers_using_requirement(self):
        class Base1: pass

        class Type1(Base1): pass

        def provider1(requirement: Requirement):
            return requirement.keys[0].type()

        class Base2:
            def __init__(self, x):
                self.x = x

        class Type2(Base2): pass

        # order here is important
        def provider2(t1: Type1, requirement: Requirement):
            return requirement.keys[0].type(t1)

        def foo(t2: Type2):
            return t2

        context = Context()
        context.add(Provider(provider1, provides_subclasses=True), provides=Base1)
        context.add(Provider(provider2, provides_subclasses=True), provides=Base2)

        t2 = context.call(foo)
        assert isinstance(t2, Type2)
        assert isinstance(t2.x, Type1)

    def test_from_return_type_annotation(self):
        def provider() -> Type1:
            return Type1()

        context = Context()
        context.add(Provider(provider))

        def returner(obj: Type1):
            return obj

        assert isinstance(context.call(returner), Type1)

    def test_no_provides(self):
        provider = Mock()
        context = Context()
        with ShouldRaise(ResourceError(
                f'Could not determine what is provided by '
                f'Provider(functools.partial({provider}), cache=True, provides_subclasses=False)'
        )):
            context.add(Provider(partial(provider)))

    def test_identifier(self):
        def provider() -> str:
            return 'some foo'

        context = Context()
        context.add(Provider(provider), identifier='param')

        def foo(param):
            return param

        compare(context.call(foo), expected='some foo')

    def test_identifier_only(self):
        def provider():
            return 'some foo'

        context = Context()
        context.add(Provider(provider), identifier='param')

        def foo(param):
            return param

        compare(context.call(foo), expected='some foo')

    def test_minimal_representation(self):
        def provider(): pass
        context = Context()
        context.add(Provider(provider), provides=str)
        expected = ("<Context: {\n"
                    f"    str: Provider({provider}, cache=True, provides_subclasses=False)\n"
                    "}>")
        compare(expected, actual=repr(context))
        compare(expected, actual=str(context))

    def test_maximal_representation(self):
        def provider() -> str: pass
        p = Provider(provider, cache=False, provides_subclasses=True)
        p.obj = 'it'
        context = Context()
        context.add(p, provides=str, identifier='the id')
        expected = ("<Context: {\n"
                    f"    'the id': Provider({provider}, "
                    f"cached='it', cache=False, provides_subclasses=True)\n"
                    f"    str, 'the id': Provider({provider}, "
                    f"cached='it', cache=False, provides_subclasses=True)\n"
                    "}>")
        compare(expected, actual=repr(context))
        compare(expected, actual=str(context))

    def test_custom_requirement(self):

        class FromRequest(Requirement):

            def __init__(self, name):
                super().__init__([ResourceKey(identifier='request')])
                self.name = name

            def process(self, obj):
                # this example doesn't show it, but this is a method so
                # there can be conditional stuff in here:
                return obj.get(self.name, missing)

        def foo(bar: str):
            return bar

        context = Context()
        context.add({'bar': 'foo'}, identifier='request')
        compare(context.call(foo, requires=FromRequest('bar')), expected='foo')
        # real world, FromRequest would have a decent repr:
        with ShouldRaise(ResourceError(
                "FromRequest(ResourceKey('request')) could not be satisfied"
        )):
            context.call(foo, requires=FromRequest('baz'))


class TestNesting:

    def test_nest(self):
        c1 = Context()
        c1.add('c1a', identifier='a')
        c1.add('c1c', identifier='c')
        c2 = c1.nest()
        c2.add('c2b', identifier='b')
        c2.add('c2c', identifier='c')

        def foo(a, b=None, c=None):
            return a, b, c

        compare(c2.call(foo), expected=('c1a', 'c2b', 'c2c'))
        compare(c1.call(foo), expected=('c1a', None, 'c1c'))

    def test_uses_existing_cached_value(self):
        class X: pass

        x_ = X()

        xs = [x_]

        def make_x():
            return xs.pop()

        c1 = Context()
        c1.add(Provider(make_x, cache=True), identifier='x')

        assert c1.call(lambda x: x) is x_
        c2 = c1.nest()
        assert c2.call(lambda x: x) is x_

        assert c2.call(lambda x: x) is x_
        assert c1.call(lambda x: x) is x_

    def test_stored_cached_value_in_nested_context(self):
        class X: pass

        x1 = X()
        x2 = X()

        xs = [x2, x1]

        def make_x():
            return xs.pop()

        c1 = Context()
        c1.add(Provider(make_x, cache=True), identifier='x')

        c2 = c1.nest()
        assert c2.call(lambda x: x) is x1
        assert c1.call(lambda x: x) is x2

        assert c1.call(lambda x: x) is x2
        assert c2.call(lambda x: x) is x1

    def test_no_cache_in_nested(self):
        class X: pass

        x1 = X()
        x2 = X()

        xs = [x2, x1]

        def make_x():
            return xs.pop()

        c1 = Context()
        c1.add(Provider(make_x, cache=False), identifier='x')

        c2 = c1.nest()
        assert c2.call(lambda x: x) is x1
        assert c2.call(lambda x: x) is x2

    def test_with_default_requirement(self):

        def make_requirement(name, type_, default) -> Requirement:
            pass

        c1 = Context(default_requirement=make_requirement)
        c2 = c1.nest()
        assert c2._default_requirement is make_requirement
