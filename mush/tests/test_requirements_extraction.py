import pytest; pytestmark = pytest.mark.skip("WIP")
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
from mush.extraction import extract_requires#, extract_returns, update_wrapper
from mush.requirements import Requirement, ItemOp
from .helpers import PY_36, Type1, Type2, Type3, Type4


def check_extract(obj, expected_rq, expected_rt):
    rq = extract_requires(obj, None)
    rt = extract_returns(obj, None)
    compare(rq, expected=expected_rq, strict=True)
    compare(rt, expected=expected_rt, strict=True)


class TestRequirementsExtraction(object):

    def test_default_requirements_for_function(self):
        def foo(a, b=None): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key='a', name='a'),
                          Value.make(key='b', default=None, name='b'),
                      )),
                      expected_rt=result_type)

    def test_default_requirements_for_class(self):
        class MyClass(object):
            def __init__(self, a, b=None): pass
        check_extract(MyClass,
                      expected_rq=RequiresType((
                          Value.make(key='a', name='a'),
                          Value.make(key='b', name='b', default=None),
                      )),
                      expected_rt=result_type)

    def test_extract_from_partial(self):
        def foo(x, y, z, a=None): pass
        p = partial(foo, 1, y=2)
        check_extract(
            p,
            expected_rq=RequiresType((
                Value.make(key='z', name='z', target='z'),
                Value.make(key='a', name='a', target='a', default=None),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_default_not_in_partial(self):
        def foo(a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequiresType((
                Value.make(key='a', name='a', default=None),
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
                Value.make(key='b', name='b'),
                Value.make(key='a', name='a', default=None),
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
                Value.make(key='a', name='a'),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_required_in_partial_kw(self):
        def foo(b, a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=RequiresType((
                Value.make(key='b', name='b'),
            )),
            expected_rt=result_type
        )


class TestExtractDeclarationsFromTypeAnnotations(object):

    def test_extract_from_annotations(self):
        def foo(a: 'foo', b, c: 'bar' = 1, d=2) -> 'bar': pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key='foo', name='a'),
                          Value.make(key='b', name='b'),
                          Value.make(key='bar', name='c', default=1),
                          Value.make(key='d', name='d', default=2)
                      )),
                      expected_rt=returns('bar'))

    def test_requires_only(self):
        def foo(a: 'foo'): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key='foo', name='a'),)),
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
                      expected_rq=RequiresType((Value.make(key='foo', name='a', default=None),)),
                      expected_rt=returns('bar'))

    def test_decorator_trumps_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: 'x') -> 'y': pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key='foo', name='a'),)),
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
                          Value.make(key='config', name='a', ops=[ItemOp('db_url')]),
                      )),
                      expected_rt=result_type)

    def test_default_requirements(self):
        def foo(a, b=1, *, c, d=None): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key='a', name='a'),
                          Value.make(key='b', name='b', default=1),
                          Value.make(key='c', name='c', target='c'),
                          Value.make(key='d', name='d', target='d', default=None)
                      )),
                      expected_rt=result_type)

    def test_type_only(self):
        class T: pass
        def foo(a: T): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key=T, name='a', type=T),)),
                      expected_rt=result_type)

    @pytest.mark.parametrize("type_", [str, int, dict, list])
    def test_simple_type_only(self, type_):
        def foo(a: type_): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key='a', name='a', type=type_),)),
                      expected_rt=result_type)

    def test_type_plus_value(self):
        def foo(a: str = Value('b')): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key='b', name='a', type=str),)),
                      expected_rt=result_type)

    def test_type_plus_value_with_default(self):
        def foo(a: str = Value('b', default=1)): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key='b', name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_plus_default(self):
        def foo(a: Value('b', type_=str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key='b', name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_in_value_key_plus_default(self):
        def foo(a: Value(str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key=str, name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_plus_default(self):
        def foo(a: Value(type_=str) = 1): pass
        check_extract(foo,
                      expected_rq=RequiresType((
                          Value.make(key='a', name='a', type=str, default=1),
                      )),
                      expected_rt=result_type)

    def test_value_unspecified_with_type(self):
        class T1: pass
        def foo(a: T1 = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key=T1, name='a', type=T1),)),
                      expected_rt=result_type)

    def test_value_unspecified_with_simple_type(self):
        def foo(a: str = Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key='a', name='a', type=str),)),
                      expected_rt=result_type)

    def test_value_unspecified(self):
        def foo(a=Value()): pass
        check_extract(foo,
                      expected_rq=RequiresType((Value.make(key='a', name='a'),)),
                      expected_rt=result_type)

    def test_requirement_modifier(self):
        def foo(x: str = None): pass

        class FromRequest(Requirement): pass

        def modifier(requirement):
            if type(requirement) is Requirement:
                requirement = FromRequest.make_from(requirement)
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
                          Value.make(key='a', name='a'),
                          Value.make(key='b', name='b', target='b'),
                          Value.make(key='c', name='c', target='c'),
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
                          Value.make(key='a', name='a', target='a'),
                          Value.make(key='b', name='b', target='b', type=str),
                          Value.make(key='c', name='c', target='c'),
                      )),
                      expected_rt=result_type)

    def test_explicit_requirement_type_trumps_default_requirement_type(self):

        class FromRequest(Requirement): pass

        @requires(a=Requirement('a'))
        def foo(a):
            pass

        compare(actual=extract_requires(foo, requires(a=FromRequest('b'))),
                strict=True,
                expected=RequiresType((
                          FromRequest.make(key='b', name='a', target='a'),
                      )))
