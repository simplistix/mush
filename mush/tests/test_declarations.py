from functools import partial
from unittest import TestCase

import pytest
from mock import Mock
from testfixtures import compare, ShouldRaise

from mush import Context
from mush.declarations import (
    requires, returns,
    returns_mapping, returns_sequence, returns_result_type,
    nothing,
    result_type, Requirement,
    Value,
    ValueAttrOp,
    RequiresType,
    ValueItemOp
)
from mush.extraction import extract_requires, extract_returns, update_wrapper
from mush.markers import missing


def check_extract(obj, expected_rq, expected_rt):
    rq = extract_requires(obj, None)
    rt = extract_returns(obj, None)
    compare(rq, expected=expected_rq, strict=True)
    compare(rt, expected=expected_rt, strict=True)


class Type1(object): pass
class Type2(object): pass
class Type3(object): pass
class Type4(object): pass


class TestRequires(TestCase):

    def test_empty(self):
        r = requires()
        compare(repr(r), 'requires()')
        compare(r, expected=[])

    def test_types(self):
        r = requires(Type1, Type2, x=Type3, y=Type4)
        compare(repr(r), 'requires(Type1, Type2, x=Type3, y=Type4)')
        compare(r, expected=[
            Requirement(Type1, type_=Type1),
            Requirement(Type2, type_=Type2),
            Requirement(Type3, name='x', type_=Type3, target='x'),
            Requirement(Type4, name='y', type_=Type4, target='y'),
        ])

    def test_strings(self):
        r = requires('1', '2', x='3', y='4')
        compare(repr(r), "requires('1', '2', x='3', y='4')")
        compare(r, expected=[
            Requirement('1'),
            Requirement('2'),
            Requirement('3', name='x', target='x'),
            Requirement('4', name='y', target='y'),
        ])

    def test_tuple_arg(self):
        with ShouldRaise(TypeError("('1', '2') is not a type or label")):
            requires(('1', '2'))

    def test_tuple_kw(self):
        with ShouldRaise(TypeError("('1', '2') is not a type or label")):
            requires(foo=('1', '2'))

    def test_decorator_paranoid(self):
        @requires(Type1)
        def foo():
            return 'bar'

        compare(foo.__mush__['requires'], expected=[Requirement(Type1, type_=Type1)])
        compare(foo(), 'bar')


class TestRequirement:

    def test_repr_minimal(self):
        compare(repr(Requirement('foo')),
                expected="Requirement('foo')")

    def test_repr_maximal(self):
        r = Requirement('foo', name='n', type_='ty', default=None, target='ta')
        r.ops.append(ValueAttrOp('bar'))
        compare(repr(r),
                expected="Requirement(Value('foo', default=None).bar, "
                         "name='n', type_='ty', target='ta')")

    def test_clone(self):
        r = Value('foo').bar.requirement
        r_ = r.clone()
        assert r_ is not r
        assert r_.ops is not r.ops
        compare(r_, expected=r)


def check_ops(value, data, *, expected):
    for op in value.requirement.ops:
        data = op(data)
    compare(expected, actual=data)


class TestValue:

    @pytest.mark.parametrize("name", ['attr', 'requirement'])
    def test_attr_special_name(self, name):
        v = Value('foo')
        assert v.attr(name) is v
        compare(v.requirement.ops, [ValueAttrOp(name)])

    @pytest.mark.parametrize("name", ['attr', 'requirement'])
    def test_item_special_name(self, name):
        v = Value('foo')
        assert v[name] is v
        compare(v.requirement.ops, [ValueItemOp(name)])

    def test_no_special_name_via_getattr(self):
        v = Value('foo')
        with ShouldRaise(AttributeError):
            assert v.__len__
        compare(v.requirement.ops, [])

    def test_type_from_key(self):
        v = Value(str)
        compare(v.requirement.type, expected=str)

    def test_key_and_type_cannot_disagree(self):
        with ShouldRaise(TypeError('type_ cannot be specified if key is a type')):
            Value(key=str, type_=int)


class TestItem:

    def test_single(self):
        h = Value(Type1)['foo']
        compare(repr(h), "Value(Type1)['foo']")
        check_ops(h, {'foo': 1}, expected=1)

    def test_multiple(self):
        h = Value(Type1)['foo']['bar']
        compare(repr(h), "Value(Type1)['foo']['bar']")
        check_ops(h, {'foo': {'bar': 1}}, expected=1)

    def test_missing_obj(self):
        h = Value(Type1)['foo']['bar']
        with ShouldRaise(TypeError):
            check_ops(h, object(), expected=None)

    def test_missing_key(self):
        h = Value(Type1)['foo']
        check_ops(h, {}, expected=missing)

    def test_passed_missing(self):
        c = Context()
        c.add({}, provides='key')
        compare(c.call(lambda x: x, requires=Value('key', default=1)['foo']['bar']),
                expected=1)

    def test_bad_type(self):
        h = Value(Type1)['foo']['bar']
        with ShouldRaise(TypeError):
            check_ops(h, [], expected=None)


class TestAttr(TestCase):

    def test_single(self):
        h = Value(Type1).foo
        compare(repr(h), "Value(Type1).foo")
        m = Mock()
        check_ops(h, m, expected=m.foo)

    def test_multiple(self):
        h = Value(Type1).foo.bar
        compare(repr(h), "Value(Type1).foo.bar")
        m = Mock()
        check_ops(h, m, expected=m.foo.bar)

    def test_missing(self):
        h = Value(Type1).foo
        compare(repr(h), "Value(Type1).foo")
        check_ops(h, object(), expected=missing)

    def test_passed_missing(self):
        c = Context()
        c.add(object(), provides='key')
        compare(c.call(lambda x: x, requires=Value('key', default=1).foo.bar),
                expected=1)


class TestReturns(TestCase):

    def test_type(self):
        r = returns(Type1)
        compare(repr(r), 'returns(Type1)')
        compare(dict(r.process('foo')), {Type1: 'foo'})

    def test_string(self):
        r = returns('bar')
        compare(repr(r), "returns('bar')")
        compare(dict(r.process('foo')), {'bar': 'foo'})

    def test_sequence(self):
        r = returns(Type1, 'bar')
        compare(repr(r), "returns(Type1, 'bar')")
        compare(dict(r.process(('foo', 'baz'))),
                {Type1: 'foo', 'bar': 'baz'})

    def test_decorator(self):
        @returns(Type1)
        def foo():
            return 'foo'
        r = foo.__mush__['returns']
        compare(repr(r), 'returns(Type1)')
        compare(dict(r.process(foo())), {Type1: 'foo'})

    def test_bad_type(self):
        with ShouldRaise(TypeError(
            '[] is not a type or label'
        )):
            @returns([])
            def foo(): pass


class TestReturnsMapping(TestCase):

    def test_it(self):
        @returns_mapping()
        def foo():
            return {Type1: 'foo', 'bar': 'baz'}
        r = foo.__mush__['returns']
        compare(repr(r), 'returns_mapping()')
        compare(dict(r.process(foo())),
                {Type1: 'foo', 'bar': 'baz'})


class TestReturnsSequence(TestCase):

    def test_it(self):
        t1 = Type1()
        t2 = Type2()
        @returns_sequence()
        def foo():
            return t1, t2
        r = foo.__mush__['returns']
        compare(repr(r), 'returns_sequence()')
        compare(dict(r.process(foo())),
                {Type1: t1, Type2: t2})


class TestReturnsResultType(TestCase):

    def test_basic(self):
        @returns_result_type()
        def foo():
            return 'foo'
        r = foo.__mush__['returns']
        compare(repr(r), 'returns_result_type()')
        compare(dict(r.process(foo())), {str: 'foo'})

    def test_old_style_class(self):
        class Type: pass
        obj = Type()
        r = returns_result_type()
        compare(dict(r.process(obj)), {Type: obj})

    def test_returns_nothing(self):
        def foo():
            pass
        r = returns_result_type()
        compare(dict(r.process(foo())), {})


class TestExtractDeclarations(object):

    def test_default_requirements_for_function(self):
        def foo(a, b=None): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('a', name='a'),
                          Requirement('b', name='b', default=None)
                      )),
                      expected_rt=result_type)

    def test_default_requirements_for_class(self):
        class MyClass(object):
            def __init__(self, a, b=None): pass
        check_extract(MyClass,
                      expected_rq=RequiresType((
                          Requirement('a', name='a'),
                          Requirement('b', name='b', default=None)
                      )),
                      expected_rt=result_type)

    def test_extract_from_partial(self):
        def foo(x, y, z, a=None): pass
        p = partial(foo, 1, y=2)
        check_extract(
            p,
            expected_rq=RequiresType((
                Requirement('z', name='z', target='z'),
                Requirement('a', name='a', target='a', default=None)
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_default_not_in_partial(self):
        def foo(a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequiresType((
                Requirement('a', name='a', default=None),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_default_in_partial_arg(self):
        def foo(a=None): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since a is already bound by the partial:
            expected_rq=nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_default_in_partial_kw(self):
        def foo(a=None): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_required_in_partial_arg(self):
        def foo(a): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since a is already bound by the partial:
            expected_rq=nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_required_in_partial_kw(self):
        def foo(a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_default_not_in_partial(self):
        def foo(b, a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequiresType((
                Requirement('b', name='b'),
                Requirement('a', name='a', default=None)
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_required_in_partial_arg(self):
        def foo(b, a): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since b is already bound:
            expected_rq=RequiresType((
                Requirement('a', name='a'),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_required_in_partial_kw(self):
        def foo(b, a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=RequiresType((
                Requirement('b', name='b'),
            )),
            expected_rt=result_type
        )


class TestExtractDeclarationsFromTypeAnnotations(object):

    def test_extract_from_annotations(self):
        def foo(a: 'foo', b, c: 'bar' = 1, d=2) -> 'bar': pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('foo', name='a'),
                          Requirement('b', name='b'),
                          Requirement('bar', name='c', default=1),
                          Requirement('d', name='d', default=2)
                      )),
                      expected_rt=returns('bar'))

    def test_requires_only(self):
        def foo(a: 'foo'): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement('foo', name='a'),)),
                      expected_rt=result_type)

    def test_returns_only(self):
        def foo() -> 'bar': pass
        check_extract(foo,
                      expected_rq=nothing,
                      expected_rt=returns('bar'))

    def test_extract_from_decorated_class(self):

        class Wrapper(object):
            def __init__(self, func):
                self.func = func
            def __call__(self):
                return 'the '+self.func()

        def my_dec(func):
            return update_wrapper(Wrapper(func), func)

        @my_dec
        def foo(a: 'foo' = None) -> 'bar':
            return 'answer'

        compare(foo(), expected='the answer')
        check_extract(foo,
                      expected_rq=RequiresType((Requirement('foo', name='a', default=None),)),
                      expected_rt=returns('bar'))

    def test_decorator_trumps_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: 'x') -> 'y': pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement('foo', name='a'),)),
                      expected_rt=returns('bar'))

    def test_returns_mapping(self):
        rt = returns_mapping()
        def foo() -> rt: pass
        check_extract(foo,
                      expected_rq=nothing,
                      expected_rt=rt)

    def test_returns_sequence(self):
        rt = returns_sequence()
        def foo() -> rt: pass
        check_extract(foo,
                      expected_rq=nothing,
                      expected_rt=rt)

    def test_how_instance_in_annotations(self):
        def foo(a: Value('config')['db_url']): pass
        requirement = Requirement('config', name='a')
        requirement.ops.append(ValueItemOp('db_url'))
        check_extract(foo,
                      expected_rq=RequiresType((requirement,)),
                      expected_rt=result_type)

    def test_default_requirements(self):
        def foo(a, b=1, *, c, d=None): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('a', name='a'),
                          Requirement('b', name='b', default=1),
                          Requirement('c', name='c', target='c'),
                          Requirement('d', name='d', target='d', default=None)
                      )),
                      expected_rt=result_type)

    def test_type_only(self):
        class T: pass
        def foo(a: T): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement(T, name='a', type_=T),)),
                      expected_rt=result_type)

    @pytest.mark.parametrize("type_", [str, int, dict, list])
    def test_simple_type_only(self, type_):
        def foo(a: type_): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement('a', name='a', type_=type_),)),
                      expected_rt=result_type)

    def test_type_plus_value(self):
        def foo(a: str = Value('b')): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement('b', name='a', type_=str),)),
                      expected_rt=result_type)

    def test_type_plus_value_with_default(self):
        def foo(a: str = Value('b', default=1)): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('b', name='a', type_=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_plus_default(self):
        def foo(a: Value('b', type_=str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('b', name='a', type_=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_in_value_key_plus_default(self):
        def foo(a: Value(str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement(key=str, name='a', type_=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_plus_default(self):
        def foo(a: Value(type_=str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement(key='a', name='a', type_=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_unspecified_with_type(self):
        class T1: pass
        def foo(a: T1 = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement(key=T1, name='a', type_=T1),)),
                      expected_rt=result_type)

    def test_value_unspecified_with_simple_type(self):
        def foo(a: str = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement(key='a', name='a', type_=str),)),
                      expected_rt=result_type)

    def test_value_unspecified(self):
        def foo(a = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((Requirement(key='a', name='a'),)),
                      expected_rt=result_type)


class TestDeclarationsFromMultipleSources:

    def test_declarations_from_different_sources(self):
        r1 = Requirement('a')
        r2 = Requirement('b')
        r3 = Requirement('c')

        @requires(b=r2)
        def foo(a: r1, b, c=r3):
            pass

        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('a', name='a'),
                          Requirement('b', name='b', target='b'),
                          Requirement('c', name='c', target='c'),
                      )),
                      expected_rt=result_type)

    def test_declaration_priorities(self):
        r1 = Requirement('a')
        r2 = Requirement('b')
        r3 = Requirement('c')

        @requires(a=r1)
        def foo(a: r2 = r3, b: str = r2, c = r3):
            pass

        check_extract(foo,
                      expected_rq=RequiresType((
                          Requirement('a', name='a', target='a'),
                          Requirement('b', name='b', target='b', type_=str),
                          Requirement('c', name='c', target='c'),
                      )),
                      expected_rt=result_type)
