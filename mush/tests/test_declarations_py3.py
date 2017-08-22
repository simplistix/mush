from testfixtures import compare

from mush.declarations import (
    requires, returns, extract_declarations, returns_mapping,
    returns_sequence, item,
    update_wrapper
)


class TestExtractDeclarations(object):

    def check_extract(self, obj, expected_rq, expected_rt):
        rq, rt = extract_declarations(obj, None, None)
        compare(rq, expected=expected_rq, strict=True)
        compare(rt, expected=expected_rt, strict=True)

    def test_extract_from_annotations(self):
        def foo(a: 'foo', b, c: 'bar' = 1, d=2) -> 'bar': pass
        self.check_extract(foo,
                           expected_rq=requires(a='foo', c='bar'),
                           expected_rt=returns('bar'))

    def test_requires_only(self):
        def foo(a: 'foo'): pass
        self.check_extract(foo,
                           expected_rq=requires(a='foo'),
                           expected_rt=None)

    def test_returns_only(self):
        def foo(a) -> 'bar': pass
        self.check_extract(foo,
                           expected_rq=None,
                           expected_rt=returns('bar'))

    def test_extract_from_decorated_class(self, mock):

        class Wrapper(object):
            def __init__(self, func):
                self.func = func
            def __call__(self):
                return 'the '+self.func()

        def my_dec(func):
            return update_wrapper(func, Wrapper(func))

        @my_dec
        def foo(a: 'foo'=None) -> 'bar':
            return 'answer'

        compare(foo(), expected='answer')
        self.check_extract(foo,
                           expected_rq=requires(a='foo'),
                           expected_rt=returns('bar'))

    def test_decorator_trumps_annotations(self):
        @requires('foo')
        @returns('bar')
        def foo(a: 'x') -> 'y': pass
        self.check_extract(foo,
                           expected_rq=requires('foo'),
                           expected_rt=returns('bar'))

    def test_returns_mapping(self):
        rt = returns_mapping()
        def foo() -> rt: pass
        self.check_extract(foo,
                           expected_rq=None,
                           expected_rt=rt)

    def test_returns_sequence(self):
        rt = returns_sequence()
        def foo() -> rt: pass
        self.check_extract(foo,
                           expected_rq=None,
                           expected_rt=rt)

    def test_how_instance_in_annotations(self):
        how = item('config', 'db_url')
        def foo(a: how): pass
        self.check_extract(foo,
                           expected_rq=requires(a=how),
                           expected_rt=None)
