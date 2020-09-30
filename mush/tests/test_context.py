# from typing import Tuple, List
#
from typing import NewType, Mapping, Any
from testfixtures.mock import Mock

from testfixtures import ShouldRaise, compare

# from testfixtures.mock import Mock
#
from mush import (
    Context, Requirement, Value, requires
)
from mush.context import ResourceError
# from mush.declarations import RequiresType, requires_nothing, returns_nothing
# from mush.requirements import Requirement
from .helpers import TheType, Type1, Type2
from ..resources import ResourceValue, Provider


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

    def tes_optional_type_present(self):
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
            return request_

        with ShouldRaise(ResourceError(
                "request_: typing.Mapping[str, typing.Any] could not be satisfied"
        )):
            context.call(returner)

    def test_requires_typing_missing_new_type(self):
        Request = NewType('Request', dict)
        context = Context()

        def returner(request_: Request):
            return request_

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

# XXX - these are for explicit requires() objects:
    # def test_call_requires_string(self):
    #     def foo(obj):
    #         return obj
    #     context = Context()
    #     context.add('bar', identifier='baz')
    #     result = context.call(foo, requires('baz'))
    #     compare(result, expected='bar')
    #     compare({'baz': 'bar'}, actual=context._store)

#     def test_call_requires_type(self):
#         def foo(obj):
#             return obj
#         context = Context()
#         context.add('bar', TheType)
#         result = context.call(foo, requires(TheType))
#         compare(result, 'bar')
#         compare({TheType: 'bar'}, actual=context._store)
#
    #
    #     def test_call_requires_accidental_tuple(self):
    #         def foo(obj): return obj
    #         context = Context()
    #         with ShouldRaise(TypeError(
    #                 "(<class 'mush.tests.helpers.TheType'>, "
    #                 "<class 'mush.tests.helpers.TheType'>) "
    #                 "is not a valid decoration type"
    #         )):
    #             context.call(foo, requires((TheType, TheType)))
#
#     def test_call_requires_optional_override_source_and_default(self):
#         def foo(x=1):
#             return x
#         context = Context()
#         context.add(2, provides='x')
#         result = context.call(foo, requires(x=Value('y', default=3)))
#         compare(result, expected=3)
#


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
            return x
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


# XXX requirements caching:
#
#     def test_call_caches_requires(self):
#         context = Context()
#         def foo(): pass
#         context.call(foo)
#         compare(context._requires_cache[foo], expected=RequiresType())
#
#     def test_call_explict_explicit_requires_no_cache(self):
#         context = Context()
#         context.add('a')
#         def foo(*args):
#             return args
#         result = context.call(foo, requires(str))
#         compare(result, ('a',))
#         compare(context._requires_cache, expected={})
#

    # XXX extract

#     def test_extract_minimal(self):
#         o = TheType()
#         def foo() -> TheType:
#             return o
#         context = Context()
#         result = context.extract(foo)
#         assert result is o
#         compare({TheType: o}, actual=context._store)
#         compare(context._requires_cache[foo], expected=RequiresType())
#         compare(context._returns_cache[foo], expected=returns(TheType))
#
#     def test_extract_maximal(self):
#         def foo(*args):
#             return args
#         context = Context()
#         context.add('a')
#         result = context.extract(foo, requires(str), returns(Tuple[str]))
#         compare(result, expected=('a',))
#         compare({
#             str: 'a',
#             Tuple[str]: ('a',),
#         }, actual=context._store)
#         compare(context._requires_cache, expected={})
#         compare(context._returns_cache, expected={})
#
#     def test_returns_single(self):
#         def foo():
#             return 'bar'
#         context = Context()
#         result = context.extract(foo, requires_nothing, returns(TheType))
#         compare(result, 'bar')
#         compare({TheType: 'bar'}, actual=context._store)
#
#     def test_returns_sequence(self):
#         def foo():
#             return 1, 2
#         context = Context()
#         result = context.extract(foo, requires_nothing, returns('foo', 'bar'))
#         compare(result, (1, 2))
#         compare({'foo': 1, 'bar': 2},
#                 actual=context._store)
#
#     def test_returns_mapping(self):
#         def foo():
#             return {'foo': 1, 'bar': 2}
#         context = Context()
#         result = context.extract(foo, requires_nothing, returns_mapping())
#         compare(result, {'foo': 1, 'bar': 2})
#         compare({'foo': 1, 'bar': 2},
#                 actual=context._store)
#
#     def test_ignore_return(self):
#         def foo():
#             return 'bar'
#         context = Context()
#         result = context.extract(foo, requires_nothing, returns_nothing)
#         compare(result, 'bar')
#         compare({}, context._store)
#
#     def test_ignore_non_iterable_return(self):
#         def foo(): pass
#         context = Context()
#         result = context.extract(foo)
#         compare(result, expected=None)
#         compare(context._store, expected={})
#

    # XXX - remove

#     def test_remove(self):
#         context = Context()
#         context.add('foo')
#         context.remove(str)
#         compare(context._store, expected={})
#
#     def test_remove_not_there_strict(self):
#         context = Context()
#         with ShouldRaise(ResourceError("Context does not contain 'foo'",
#                                        key='foo')):
#             context.remove('foo')
#         compare(context._store, expected={})
#
#     def test_remove_not_there_not_strict(self):
#         context = Context()
#         context.remove('foo', strict=False)
#         compare(context._store, expected={})
#
# XXX - nest
#
#     def test_nest(self):
#         c1 = Context()
#         c1.add('a', provides='a')
#         c1.add('c', provides='c')
#         c2 = c1.nest()
#         c2.add('b', provides='b')
#         c2.add('d', provides='c')
#         compare(c2.get('a'), expected='a')
#         compare(c2.get('b'), expected='b')
#         compare(c2.get('c'), expected='d')
#         compare(c1.get('a'), expected='a')
#         compare(c1.get('b', default=None), expected=None)
#         compare(c1.get('c'), expected='c')
#
#     def test_nest_with_overridden_default_requirement_type(self):
#         def modifier(): pass
#         c1 = Context(modifier)
#         c2 = c1.nest()
#         assert c2.requirement_modifier is modifier
#
#     def test_nest_with_explicit_default_requirement_type(self):
#         def modifier1(): pass
#         def modifier2(): pass
#         c1 = Context(modifier1)
#         c2 = c1.nest(modifier2)
#         assert c2.requirement_modifier is modifier2
#
#     def test_nest_keeps_declarations_cache(self):
#         c1 = Context()
#         c2 = c1.nest()
#         assert c2._requires_cache is c1._requires_cache
#         assert c2._returns_cache is c1._returns_cache
#  - XXX nesting versus cached providers!

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
        def provider(): pass
        context = Context()
        with ShouldRaise(ResourceError(f'Could not determine what is provided by {provider}')):
            context.add(Provider(provider))

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

# XXX "custom requirement" stuff
#
#     def test_custom_requirement(self):
#
#         class FromRequest(Requirement):
#             def resolve(self, context):
#                 return context.get('request')[self.key]
#
#         def foo(bar: FromRequest('bar')):
#             return bar
#
#         context = Context()
#         context.add({'bar': 'foo'}, provides='request')
#         compare(context.call(foo), expected='foo')
#
#     def test_custom_requirement_returns_missing(self):
#
#         class FromRequest(Requirement):
#             def resolve(self, context):
#                 return context.get('request').get(self.key, missing)
#
#         def foo(bar: FromRequest('bar')):
#             pass
#
#         context = Context()
#         context.add({}, provides='request')
#         with ShouldRaise(ResourceError("No FromRequest('bar') in context",
#                                        key='bar',
#                                        requirement=FromRequest.make(key='bar', name='bar'))):
#             compare(context.call(foo))
