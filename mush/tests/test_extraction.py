from functools import partial
from typing import Tuple, get_type_hints
from unittest import TestCase

import pytest
from testfixtures import compare, ShouldRaise

from mush import Value, missing
from mush.declarations import (
    requires, returns,
    returns_mapping, returns_sequence, returns_result_type,
    requires_nothing,
    result_type, Requirements, Parameter
)
from mush.extraction import extract_requires, extract_returns, update_wrapper
from mush.requirements import Requirement, ItemOp
from .helpers import PY_36, Type1, Type2, Type3, Type4
from ..resources import ResourceKey


def check_extract(obj, expected_rq, expected_rt):
    rq = extract_requires(obj)
    rt = extract_returns(obj, None)
    compare(rq, expected=expected_rq, strict=True)
    assert rt is None
    # compare(rt, expected=expected_rt, strict=True)


class TestRequirementsExtraction(object):

    def test_default_requirements_for_function(self):
        def foo(a, b=None): pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(identifier='a')),
                          Parameter(Value(identifier='b', default=None), default=None),
                      )),
                      expected_rt=result_type)

    def test_default_requirements_for_class(self):
        class MyClass(object):
            def __init__(self, a, b=None): pass
        check_extract(MyClass,
                      expected_rq=Requirements((
                          Parameter(Value(identifier='a')),
                          Parameter(Value(identifier='b', default=None), default=None),
                      )),
                      expected_rt=result_type)

    def test_extract_from_partial(self):
        def foo(x, y, z, a=None): pass
        p = partial(foo, 1, y=2)
        check_extract(
            p,
            expected_rq=Requirements((
                Parameter(Value(identifier='z'), target='z'),
                Parameter(Value(identifier='a', default=None), target='a', default=None),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_default_not_in_partial(self):
        def foo(a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=Requirements((
                Parameter(Value(identifier='a', default=None), default=None),
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
            expected_rq=Requirements((
                Parameter(Value(identifier='b')),
                Parameter(Value(identifier='a', default=None), default=None),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_required_in_partial_arg(self):
        def foo(b, a): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since b is already bound:
            expected_rq=Requirements((
                Parameter(Value(identifier='a')),
            )),
            expected_rt=result_type
        )

    def test_extract_from_partial_plus_one_required_in_partial_kw(self):
        def foo(b, a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=Requirements((
                Parameter(Value(identifier='b')),
            )),
            expected_rt=result_type
        )


# https://bugs.python.org/issue41872
def foo(a: 'Foo') -> 'Bar': pass
class Foo: pass
class Bar: pass


class TestExtractDeclarationsFromTypeAnnotations(object):

    def test_extract_from_annotations(self):
        def foo(a: Type1, b, c: Type2 = 1, d=2) -> Type3: pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(Type1, identifier='a')),
                          Parameter(Value(identifier='b')),
                          Parameter(Value(Type2, identifier='c', default=1), default=1),
                          Parameter(Value(identifier='d', default=2), default=2),
                      )),
                      expected_rt=returns('bar'))

    def test_forward_type_references(self):
        check_extract(foo,
                      expected_rq=Requirements((Parameter(Value(Foo, identifier='a')),)),
                      expected_rt=returns(Bar))

    def test_requires_only(self):
        def foo(a: Type1): pass
        check_extract(foo,
                      expected_rq=Requirements((Parameter(Value(Type1, identifier='a')),)),
                      expected_rt=result_type)

    def test_returns_only(self):
        def foo() -> Type1: pass
        check_extract(foo,
                      expected_rq=requires_nothing,
                      expected_rt=returns(Type1))

    def test_extract_from_decorated_class(self):

        class Wrapper(object):
            def __init__(self, func):
                self.func = func
            def __call__(self):
                return 'the '+self.func()

        def my_dec(func):
            return update_wrapper(Wrapper(func), func)

        @my_dec
        @requires(a=Value('foo'))
        @returns('bar')
        def foo(a=None):
            return 'answer'

        compare(foo(), expected='the answer')
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(identifier='foo'), target='a'),
                      )),
                      expected_rt=returns('bar'))

    def test_decorator_trumps_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: Type1) -> Type2: pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(identifier='foo')),)
                      ),
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
                      expected_rq=Requirements((
                          Parameter(Value(identifier='config')['db_url']),
                      )),
                      expected_rt=result_type)

    def test_default_requirements(self):
        def foo(a, b=1, *, c, d=None): pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(identifier='a')),
                          Parameter(Value(identifier='b', default=1), default=1),
                          Parameter(Value(identifier='c'), target='c'),
                          Parameter(Value(identifier='d', default=None), target='d', default=None)
                      )),
                      expected_rt=result_type)

    def test_type_only(self):
        class T: pass
        def foo(a: T): pass
        check_extract(foo,
                      expected_rq=Requirements((Parameter(Value(T, identifier='a')),)),
                      expected_rt=result_type)

    @pytest.mark.parametrize("type_", [str, int, dict, list])
    def test_simple_type_only(self, type_):
        def foo(a: type_): pass
        check_extract(foo,
                      expected_rq=Requirements((Parameter(Value(type_, identifier='a')),)),
                      expected_rt=result_type)

    def test_type_plus_value(self):
        def foo(a: str = Value('b')): pass
        check_extract(foo,
                      expected_rq=Requirements((Parameter(Value(identifier='b')),)),
                      expected_rt=result_type)

    def test_type_plus_value_with_default(self):
        def foo(a: str = Value('b', default=1)): pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(identifier='b', default=1), default=1),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_plus_default(self):
        def foo(a: Value(str, identifier='b') = 1): pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(str, identifier='b'), default=1),
                      )),
                      expected_rt=result_type)

    def test_requirement_default_preferred_to_annotation_default(self):
        def foo(a: Value(str, identifier='b', default=2) = 1): pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(str, identifier='b', default=2), default=2),
                      )),
                      expected_rt=result_type)

    def test_value_annotation_just_type_in_value_key_plus_default(self):
        def foo(a: Value(str) = 1): pass
        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(Value(str), default=1),
                      )),
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
                      expected_rq=Requirements((
                          Parameter(Requirement(default='a'), default='a'),
                          Parameter(Requirement(default='b'), default='b', target='b'),
                          Parameter(Requirement(default='c'), default='c', target='c'),
                      )),
                      expected_rt=result_type)

    def test_declaration_priorities(self):
        r1 = Requirement(missing, ResourceKey(identifier='x'))
        r2 = Requirement(missing, ResourceKey(identifier='y'))
        r3 = Requirement(missing, ResourceKey(identifier='z'))

        @requires(a=r1)
        def foo(a: r2 = r3, b: str = r2, c=r3):
            pass

        check_extract(foo,
                      expected_rq=Requirements((
                          Parameter(r1, target='a'),
                          Parameter(r2, target='b'),
                          Parameter(r3, target='c'),
                      )),
                      expected_rt=result_type)
