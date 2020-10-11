from functools import partial
from typing import Optional, Any
from testfixtures.mock import Mock

import pytest
from testfixtures import compare

from mush import Value, update_wrapper
from mush.declarations import (
    requires, returns, requires_nothing, RequirementsDeclaration, Parameter, ReturnsDeclaration,
    returns_nothing
)
from mush.extraction import extract_requires, extract_returns
from mush.requirements import Requirement, Annotation
from .helpers import Type1, Type2, Type3
from ..resources import ResourceKey
from ..typing import Type_

returns_foo = ReturnsDeclaration([ResourceKey(identifier='foo')])


def check_extract(obj, expected_rq, expected_rt=returns_foo):
    rq = extract_requires(obj)
    rt = extract_returns(obj)
    compare(rq, expected=expected_rq, strict=True)
    compare(rt, expected=expected_rt, strict=True)


class TestRequirementsExtraction:

    def test_default_requirements_for_function(self):
        def foo(a, b=None): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a')),
                          Parameter(Annotation('b', default=None), default=None),
                      )))

    def test_default_requirements_for_class(self):
        class MyClass(object):
            def __init__(self, a, b=None): pass
        check_extract(MyClass,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a')),
                          Parameter(Annotation('b', default=None), default=None),
                      )),
                      expected_rt=ReturnsDeclaration([
                          ResourceKey(MyClass),
                          ResourceKey(identifier='MyClass'),
                          ResourceKey(MyClass, 'MyClass'),
                      ]))

    def test_extract_from_partial(self):
        def foo(x, y, z, a=None): pass
        p = partial(foo, 1, y=2)
        check_extract(
            p,
            expected_rq=RequirementsDeclaration((
                Parameter(Annotation('z'), target='z'),
                Parameter(Annotation('a', default=None), target='a', default=None),
            ))
        )

    def test_extract_from_partial_default_not_in_partial(self):
        def foo(a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequirementsDeclaration((
                Parameter(Annotation('a', default=None), default=None),
            ))
        )

    def test_extract_from_partial_default_in_partial_arg(self):
        def foo(a=None): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since a is already bound by the partial:
            expected_rq=requires_nothing
        )

    def test_extract_from_partial_default_in_partial_kw(self):
        def foo(a=None): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=requires_nothing
        )

    def test_extract_from_partial_required_in_partial_arg(self):
        def foo(a): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since a is already bound by the partial:
            expected_rq=requires_nothing
        )

    def test_extract_from_partial_required_in_partial_kw(self):
        def foo(a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=requires_nothing
        )

    def test_extract_from_partial_plus_one_default_not_in_partial(self):
        def foo(b, a=None): pass
        p = partial(foo)
        check_extract(
            p,
            expected_rq=RequirementsDeclaration((
                Parameter(Annotation('b')),
                Parameter(Annotation('a', default=None), default=None),
            ))
        )

    def test_extract_from_partial_plus_one_required_in_partial_arg(self):
        def foo(b, a): pass
        p = partial(foo, 1)
        check_extract(
            p,
            # since b is already bound:
            expected_rq=RequirementsDeclaration((
                Parameter(Annotation('a')),
            ))
        )

    def test_extract_from_partial_plus_one_required_in_partial_kw(self):
        def foo(b, a): pass
        p = partial(foo, a=1)
        check_extract(
            p,
            expected_rq=RequirementsDeclaration((
                Parameter(Annotation('b')),
            ))
        )

    def test_extract_from_mock(self):
        foo = Mock()
        check_extract(
            foo,
            expected_rq=requires_nothing,
            expected_rt=returns_nothing,
        )


# https://bugs.python.org/issue41872
def foo_(a: 'Foo') -> 'Bar': pass
class Foo: pass
class Bar: pass


class TestExtractDeclarationsFromTypeAnnotations:

    def test_extract_from_annotations(self):
        def foo(a: Type1, b, c: Type2 = 1, d=2) -> Type3: pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a', Type1), type_=Type1),
                          Parameter(Annotation('b')),
                          Parameter(Annotation('c', Type2, default=1), type_=Type2, default=1),
                          Parameter(Annotation('d', default=2), default=2),
                      )),
                      expected_rt=ReturnsDeclaration([
                          ResourceKey(Type3),
                          ResourceKey(identifier='foo'),
                          ResourceKey(Type3, 'foo'),
                      ]))

    def test_forward_type_references(self):
        check_extract(foo_,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a', Foo), type_=Foo),
                      )),
                      expected_rt=ReturnsDeclaration([
                          ResourceKey(Bar),
                          ResourceKey(identifier='foo_'),
                          ResourceKey(Bar, 'foo_'),
                      ]))

    def test_requires_only(self):
        def foo(a: Type1): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a', Type1), type_=Type1),
                      )))

    def test_returns_only(self):
        def foo() -> Type1: pass
        check_extract(foo,
                      expected_rq=requires_nothing,
                      expected_rt=ReturnsDeclaration([
                          ResourceKey(Type1),
                          ResourceKey(identifier='foo'),
                          ResourceKey(Type1, 'foo'),
                      ]))

    def test_returns_nothing(self):
        def foo() -> None: pass
        check_extract(foo,
                      expected_rq=requires_nothing,
                      expected_rt=ReturnsDeclaration())

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
                      expected_rq=RequirementsDeclaration((
                          Parameter(Value(identifier='foo'), target='a'),
                      )),
                      expected_rt=ReturnsDeclaration([ResourceKey(identifier='bar')]))

    def test_decorator_preferred_to_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: Type1) -> Type2: pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Value(identifier='foo'), type_=Type1),)
                      ),
                      expected_rt=ReturnsDeclaration([ResourceKey(identifier='bar')]))

    def test_default_requirements(self):
        def foo(a, b=1, *, c, d=None): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a')),
                          Parameter(Annotation('b', default=1), default=1),
                          Parameter(Annotation('c'), target='c'),
                          Parameter(Annotation('d', default=None), target='d', default=None)
                      )))

    def test_type_only(self):
        class T: pass
        def foo(a: T): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a', T), type_=T),
                      )),
                      expected_rt=ReturnsDeclaration([ResourceKey(identifier='foo')]))

    @pytest.mark.parametrize("type_", [str, int, dict, list])
    def test_simple_type_only(self, type_):
        def foo(a: type_): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a', type_), type_=type_),
                      )))

    def test_type_plus_value(self):
        def foo(a: str = Value('b')): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Value(identifier='b'), type_=str),
                      )))

    def test_type_plus_value_with_default(self):
        def foo(a: str = Value('b', default=1)): pass
        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Value(identifier='b', default=1), type_=str, default=1),
                      )))


class Path(Requirement):

    def __init__(self, name=None, type_=None):
        super().__init__(())
        self.name=name
        self.type=type_

    def complete(self, name: str, type_: Type_, default: Any):
        return type(self)(name=name, type_=type_)


class TestCustomRequirementCompletion:

    def test_use_name(self):
        def foo(bar=Path()): pass
        check_extract(foo, RequirementsDeclaration((
            Parameter(Path(name='bar', type_=None)),
        )))

    def test_use_type(self):
        def foo(bar: str = Path()): pass
        check_extract(foo, RequirementsDeclaration((
            Parameter(Path(name='bar', type_=str), type_=str),
        )))

    def test_precedence(self):
        class PathSubclass(Path): pass
        @requires(PathSubclass())
        def foo(bar: str = Path()): pass
        check_extract(foo, RequirementsDeclaration((
            Parameter(PathSubclass(name='bar', type_=str), type_=str),
        )))


def it():
    pass


class TestExplicitDeclarations:

    def test_requires_from_string(self):
        compare(extract_requires(it, 'bar'), strict=True, expected=RequirementsDeclaration((
            Parameter(Value(identifier='bar')),
        )))

    def test_requires_from_type(self):
        compare(extract_requires(it, Type1), strict=True, expected=RequirementsDeclaration((
            Parameter(Value(Type1)),
        )))

    def test_requires_requirement(self):
        compare(extract_requires(it, Value(Type1, 'bar')), strict=True, expected=RequirementsDeclaration((
            Parameter(Value(Type1, 'bar')),
        )))

    def test_requires_from_tuple(self):
        compare(extract_requires(it, ('bar', 'baz')), strict=True, expected=RequirementsDeclaration((
            Parameter(Value(identifier='bar')),
            Parameter(Value(identifier='baz')),
        )))

    def test_requires_from_list(self):
        compare(extract_requires(it, ['bar', 'baz']), strict=True, expected=RequirementsDeclaration((
            Parameter(Value(identifier='bar')),
            Parameter(Value(identifier='baz')),
        )))

    def test_explicit_requires_where_parameter_has_default(self):
        def foo(x=1): pass
        compare(extract_requires(foo, 'bar'), strict=True, expected=RequirementsDeclaration((
            # default is not longer considered:
            Parameter(Value(identifier='bar')),
        )))

    def test_returns_from_string(self):
        compare(extract_returns(it, 'bar'), strict=True, expected=ReturnsDeclaration([
            ResourceKey(identifier='bar')
        ]))

    def test_returns_from_type(self):
        compare(extract_returns(it, Type1), strict=True, expected=ReturnsDeclaration([
            ResourceKey(Type1)
        ]))


class TestDeclarationsFromMultipleSources:

    def test_declarations_from_different_sources(self):
        r1 = Requirement(keys=(), default='b')
        r2 = Requirement(keys=(), default='c')

        @requires(b=r1)
        def foo(a: str, b, c=r2):
            pass

        check_extract(foo,
                      expected_rq=RequirementsDeclaration((
                          Parameter(Annotation('a', str), type_=str),
                          Parameter(Requirement((), default='b'), default='b', target='b'),
                          Parameter(Requirement((), default='c'), default='c', target='c'),
                      )))

    def test_declaration_priorities(self):
        r1 = Requirement([ResourceKey(identifier='x')])
        r2 = Requirement([ResourceKey(identifier='y')])
        r3 = Requirement([ResourceKey(identifier='z')])

        @requires(a=r1)
        @returns('bar')
        def foo(a: int = r3, b: str = r2, c=r3) -> Optional[Type1]:
            pass

        check_extract(
            foo,
            expected_rq=RequirementsDeclaration((
                Parameter(Requirement([ResourceKey(identifier='x')]), type_=int, target='a'),
                Parameter(Requirement([ResourceKey(identifier='y')]), type_=str, target='b'),
                Parameter(Requirement([ResourceKey(identifier='z')]), target='c'),
            )),
            expected_rt=ReturnsDeclaration([ResourceKey(identifier='bar')])
        )
