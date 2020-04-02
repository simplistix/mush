from functools import partial
from typing import Tuple
from unittest import TestCase

import pytest
from testfixtures import compare, ShouldRaise

from mush import Value
from mush.declarations import (
    requires, returns,
    returns_mapping, returns_sequence, returns_result_type,
    requires_nothing,
    result_type, RequiresType
)
from mush.extraction import extract_requires, extract_returns, update_wrapper
from mush.requirements import Requirement, ItemOp
from .helpers import r, PY_36, Type1, Type2, Type3, Type4


def check_extract(obj, expected_rq, expected_rt):
    rq = extract_requires(obj, None)
    rt = extract_returns(obj, None)
    compare(rq, expected=expected_rq, strict=True)
    compare(rt, expected=expected_rt, strict=True)


class TestRequires(TestCase):

    def test_empty(self):
        r = requires()
        compare(repr(r), 'requires()')
        compare(r, expected=[])

    def test_types(self):
        r_ = requires(Type1, Type2, x=Type3, y=Type4)
        compare(repr(r_), 'requires(Type1, Type2, x=Type3, y=Type4)')
        compare(r_, expected=[
            Value(Type1),
            Value(Type2),
            r(Value(Type3), name='x', target='x'),
            r(Value(Type4), name='y', target='y'),
        ])

    def test_strings(self):
        r_ = requires('1', '2', x='3', y='4')
        compare(repr(r_), "requires('1', '2', x='3', y='4')")
        compare(r_, expected=[
            Value('1'),
            Value('2'),
            r(Value('3'), name='x', target='x'),
            r(Value('4'), name='y', target='y'),
        ])

    def test_typing(self):
        r_ = requires(Tuple[str])
        text = 'Tuple' if PY_36 else 'typing.Tuple[str]'
        compare(repr(r_), f"requires({text})")
        compare(r_, expected=[r(Value(Tuple[str]), type=Tuple[str])])

    def test_tuple_arg(self):
        with ShouldRaise(TypeError("('1', '2') is not a valid decoration type")):
            requires(('1', '2'))

    def test_tuple_kw(self):
        with ShouldRaise(TypeError("('1', '2') is not a valid decoration type")):
            requires(foo=('1', '2'))

    def test_decorator_paranoid(self):
        @requires(Type1)
        def foo():
            return 'bar'

        compare(foo.__mush__['requires'], expected=[Value(Type1)])
        compare(foo(), 'bar')


class TestReturns(TestCase):

    def test_type(self):
        r = returns(Type1)
        compare(repr(r), 'returns(Type1)')
        compare(dict(r.process('foo')), {Type1: 'foo'})

    def test_string(self):
        r = returns('bar')
        compare(repr(r), "returns('bar')")
        compare(dict(r.process('foo')), {'bar': 'foo'})

    def test_typing(self):
        r = returns(Tuple[str])
        text = 'Tuple' if PY_36 else 'typing.Tuple[str]'
        compare(repr(r), f'returns({text})')
        compare(dict(r.process('foo')), {Tuple[str]: 'foo'})

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
            '[] is not a valid decoration type'
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
                          r(Value('a'), name='a'),
                          r(Value('b'), default=None, name='b'),
                      )),
                      expected_rt=result_type)

    def test_default_requirements_for_class(self):
        class MyClass(object):
            def __init__(self, a, b=None): pass
        check_extract(MyClass,
                      expected_rq=RequiresType((
                          r(Value('a'), name='a'),
                          r(Value('b'), name='b', default=None),
                      )),
                      expected_rt=result_type)

    def test_extract_from_partial(self):
        def foo(x, y, z, a=None): pass
        p = partial(foo, 1, y=2)
        check_extract(
            p,
            expected_rq=RequiresType((
                r(Value('z'), name='z', target='z'),
                r(Value('a'), name='a', target='a', default=None),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_default_not_in_partial(self):
        def foo(a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequiresType((
                r(Value('a'), name='a', default=None),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_default_in_partial_arg(self):
        def foo(a=None): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since a is already bound by the partial:
            expected_rq=requires_nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_default_in_partial_kw(self):
        def foo(a=None): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=requires_nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_required_in_partial_arg(self):
        def foo(a): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since a is already bound by the partial:
            expected_rq=requires_nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_required_in_partial_kw(self):
        def foo(a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=requires_nothing,
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_default_not_in_partial(self):
        def foo(b, a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequiresType((
                r(Value('b'), name='b'),
                r(Value('a'), name='a', default=None),
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
                r(Value('a'), name='a'),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_required_in_partial_kw(self):
        def foo(b, a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=RequiresType((
                r(Value('b'), name='b'),
            )),
            expected_rt=result_type
        )


class TestExtractDeclarationsFromTypeAnnotations(object):

    def test_extract_from_annotations(self):
        def foo(a: 'foo', b, c: 'bar' = 1, d=2) -> 'bar': pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value('foo'), name='a'),
                          r(Value('b'), name='b'),
                          r(Value('bar'), name='c', default=1),
                          r(Value('d'), name='d', default=2)
                      )),
                      expected_rt=returns('bar'))

    def test_requires_only(self):
        def foo(a: 'foo'): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value('foo'), name='a'),)),
                      expected_rt=result_type)

    def test_returns_only(self):
        def foo() -> 'bar': pass
        check_extract(foo,
                      expected_rq=requires_nothing,
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
                      expected_rq=RequiresType((r(Value('foo'), name='a', default=None),)),
                      expected_rt=returns('bar'))

    def test_decorator_trumps_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: 'x') -> 'y': pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value('foo'), name='a'),)),
                      expected_rt=returns('bar'))

    def test_returns_mapping(self):
        rt = returns_mapping()
        def foo() -> rt: pass
        check_extract(foo,
                      expected_rq=requires_nothing,
                      expected_rt=rt)

    def test_returns_sequence(self):
        rt = returns_sequence()
        def foo() -> rt: pass
        check_extract(foo,
                      expected_rq=requires_nothing,
                      expected_rt=rt)

    def test_how_instance_in_annotations(self):
        def foo(a: Value('config')['db_url']): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value('config'), name='a', ops=[ItemOp('db_url')]),
                      )),
                      expected_rt=result_type)

    def test_default_requirements(self):
        def foo(a, b=1, *, c, d=None): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value('a'), name='a'),
                          r(Value('b'), name='b', default=1),
                          r(Value('c'), name='c', target='c'),
                          r(Value('d'), name='d', target='d', default=None)
                      )),
                      expected_rt=result_type)

    def test_type_only(self):
        class T: pass
        def foo(a: T): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value(T), name='a', type=T),)),
                      expected_rt=result_type)

    @pytest.mark.parametrize("type_", [str, int, dict, list])
    def test_simple_type_only(self, type_):
        def foo(a: type_): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value('a'), name='a', type=type_),)),
                      expected_rt=result_type)

    def test_type_plus_value(self):
        def foo(a: str = Value('b')): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value('b'), name='a', type=str),)),
                      expected_rt=result_type)

    def test_type_plus_value_with_default(self):
        def foo(a: str = Value('b', default=1)): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value('b'), name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_plus_default(self):
        def foo(a: Value('b', type_=str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value('b'), name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_in_value_key_plus_default(self):
        def foo(a: Value(str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value(str), name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_plus_default(self):
        def foo(a: Value(type_=str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          r(Value(key='a'), name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_unspecified_with_type(self):
        class T1: pass
        def foo(a: T1 = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value(key=T1), name='a', type=T1),)),
                      expected_rt=result_type)

    def test_value_unspecified_with_simple_type(self):
        def foo(a: str = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value(key='a'), name='a', type=str),)),
                      expected_rt=result_type)

    def test_value_unspecified(self):
        def foo(a = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((r(Value(key='a'), name='a'),)),
                      expected_rt=result_type)

    def test_requirement_modifier(self):
        def foo(x: str = None): pass

        class FromRequest(Requirement): pass

        def modifier(requirement):
            if requirement.__class__ is Requirement:
                requirement.__class__ = FromRequest
            return requirement

        rq = extract_requires(foo, modifier=modifier)
        compare(rq, strict=True, expected=RequiresType((
            FromRequest(key='x', name='x', type_=str, default=None),
        )))


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
                          r(Value('a'), name='a'),
                          r(Value('b'), name='b', target='b'),
                          r(Value('c'), name='c', target='c'),
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
                          r(Value('a'), name='a', target='a'),
                          r(Value('b'), name='b', target='b', type=str),
                          r(Value('c'), name='c', target='c'),
                      )),
                      expected_rt=result_type)
