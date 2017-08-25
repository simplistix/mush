from testfixtures import compare

from mush.declarations import (
    requires, returns, returns_mapping, returns_sequence, item, update_wrapper,
    optional
)
from mush.tests.test_declarations import check_extract


class TestExtractDeclarations(object):

    def test_extract_from_annotations(self):
        def foo(a: 'foo', b, c: 'bar' = 1, d=2) -> 'bar': pass
        check_extract(foo,
                      expected_rq=requires(a='foo', c='bar'),
                      expected_rt=returns('bar'))

    def test_requires_only(self):
        def foo(a: 'foo'): pass
        check_extract(foo,
                      expected_rq=requires(a='foo'),
                      expected_rt=None)

    def test_returns_only(self):
        def foo() -> 'bar': pass
        check_extract(foo,
                      expected_rq=None,
                      expected_rt=returns('bar'))

    def test_extract_from_decorated_class(self, mock):

        class Wrapper(object):
            def __init__(self, func):
                self.func = func
            def __call__(self):
                return 'the '+self.func()

        def my_dec(func):
            return update_wrapper(Wrapper(func), func)

        @my_dec
        def foo(a: 'foo'=None) -> 'bar':
            return 'answer'

        compare(foo(), expected='the answer')
        check_extract(foo,
                      expected_rq=requires(a='foo'),
                      expected_rt=returns('bar'))

    def test_decorator_trumps_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: 'x') -> 'y': pass
        check_extract(foo,
                      expected_rq=requires('foo'),
                      expected_rt=returns('bar'))

    def test_returns_mapping(self):
        rt = returns_mapping()
        def foo() -> rt: pass
        check_extract(foo,
                      expected_rq=None,
                      expected_rt=rt)

    def test_returns_sequence(self):
        rt = returns_sequence()
        def foo() -> rt: pass
        check_extract(foo,
                      expected_rq=None,
                      expected_rt=rt)

    def test_how_instance_in_annotations(self):
        how = item('config', 'db_url')
        def foo(a: how): pass
        check_extract(foo,
                      expected_rq=requires(a=how),
                      expected_rt=None)

    def test_default_requirements(self):
        def foo(a, b=1, *, c, d=None): pass
        check_extract(foo,
                      expected_rq=requires('a',
                                           optional('b'),
                                           c='c',
                                           d=optional('d')),
                      expected_rt=None)
