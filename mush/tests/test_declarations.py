from typing import Tuple
from unittest import TestCase

from testfixtures import compare, ShouldRaise

from mush import Value, AnyOf
from mush.declarations import requires, returns, Parameter, RequirementsDeclaration, \
    ReturnsDeclaration
from .helpers import PY_36, Type1, Type2, Type3, Type4
from ..resources import ResourceKey


class TestRequires(TestCase):

    def test_empty(self):
        r = requires()
        compare(repr(r), 'requires()')
        compare(r, expected=[])

    def test_types(self):
        r_ = requires(Type1, Type2, x=Type3, y=Type4)
        compare(repr(r_), 'requires(Value(Type1), Value(Type2), x=Value(Type3), y=Value(Type4))')
        compare(r_, expected=[
            Parameter(Value(Type1)),
            Parameter(Value(Type2)),
            Parameter(Value(Type3), target='x'),
            Parameter(Value(Type4), target='y'),
        ])

    def test_strings(self):
        r_ = requires('1', '2', x='3', y='4')
        compare(repr(r_), "requires(Value('1'), Value('2'), x=Value('3'), y=Value('4'))")
        compare(r_, expected=[
            Parameter(Value('1')),
            Parameter(Value('2')),
            Parameter(Value('3'), target='x'),
            Parameter(Value('4'), target='y'),
        ])

    def test_typing(self):
        r_ = requires(Tuple[str])
        text = 'Tuple' if PY_36 else 'typing.Tuple[str]'
        compare(repr(r_),expected=f"requires(Value({text}))")
        compare(r_, expected=[Parameter(Value(Tuple[str]))])

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

        compare(foo.__mush__['requires'], expected=[Parameter(Value(Type1))])
        compare(foo(), 'bar')

    def test_requirement_instance(self):
        compare(requires(x=AnyOf('foo', 'bar')),
                expected=RequirementsDeclaration([Parameter(AnyOf('foo', 'bar'), target='x')]),
                strict=True)


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
