from typing import Tuple
from unittest.case import TestCase

import pytest
from testfixtures import compare, ShouldRaise
from testfixtures.mock import Mock

from mush import Context, Call, Value, missing, requires, ResourceError
from mush.requirements import Requirement, AttrOp, ItemOp, AnyOf, Like
from .helpers import Type1


def check_ops(value, data, *, expected):
    for op in value.ops:
        data = op(data)
    compare(expected, actual=data)


class TestRequirement:

    def test_repr_minimal(self):
        compare(repr(Requirement('foo')),
                expected="Requirement('foo')")

    def test_repr_maximal(self):
        r = Requirement('foo', name='n', type_='ty', default=None, target='ta')
        r.ops.append(AttrOp('bar'))
        compare(repr(r),
                expected="Requirement('foo', default=None).bar")

    def test_make_allows_params_not_passed_to_constructor(self):
        r = Value.make(key='x', target='a')
        assert type(r) is Value
        compare(r.key, expected='x')
        compare(r.target, expected='a')

    def test_make_can_create_invalid_objects(self):
        # So be careful!

        class SampleRequirement(Requirement):
            def __init__(self, foo):
                super().__init__(key='y')
                self.foo = foo

        r = SampleRequirement('it')
        compare(r.foo, expected='it')

        r = SampleRequirement.make(key='x')
        assert 'foo' not in r.__dict__
        # ...when it really should be!

    def test_clone_using_make_from(self):
        r = Value('foo').bar.requirement
        r_ = r.make_from(r)
        assert r_ is not r
        assert r_.ops is not r.ops
        compare(r_, expected=r)

    def test_make_from_with_mutable_default(self):
        r = Requirement('foo', default=[])
        r_ = r.make_from(r)
        assert r_ is not r
        assert r_.default is not r.default
        compare(r_, expected=r)

    def test_make_from_into_new_type(self):
        r = Requirement('foo').bar.requirement
        r_ = Value.make_from(r)
        compare(r_, expected=Value('foo').bar.requirement)

    def test_make_from_with_required_constructor_parameter(self):

        class SampleRequirement(Requirement):
            def __init__(self, foo):
                super().__init__('foo')
                self.foo = foo

        r = Requirement('foo')
        r_ = SampleRequirement.make_from(r, foo='it')
        assert r_ is not r
        compare(r_, expected=SampleRequirement(foo='it'))

    def test_make_from_source_has_more_attributes(self):

        class SampleRequirement(Requirement):
            def __init__(self, foo):
                super().__init__('bar')
                self.foo = foo

        r = SampleRequirement('it')
        r_ = Requirement.make_from(r)
        assert r_ is not r

        assert r_.key == 'bar'
        # while this is a bit ugly, it will hopefully do no harm:
        assert r_.foo == 'it'

    special_names = ['attr', 'ops', 'target']

    @pytest.mark.parametrize("name", special_names)
    def test_attr_special_name(self, name):
        v = Requirement('foo')
        assert getattr(v, name) is not self
        assert v.attr(name) is v
        compare(v.ops, expected=[AttrOp(name)])

    @pytest.mark.parametrize("name", special_names)
    def test_item_special_name(self, name):
        v = Requirement('foo')
        assert v[name] is v
        compare(v.ops, expected=[ItemOp(name)])

    def test_no_special_name_via_getattr(self):
        v = Requirement('foo')
        with ShouldRaise(AttributeError):
            assert v.__len__
        compare(v.ops, [])

    def test_resolve(self):
        r = Requirement('foo')
        with ShouldRaise(NotImplementedError):
            r.resolve(None)


class TestValue:

    def test_type_from_key(self):
        v = Value(str)
        compare(v.requirement.type, expected=str)

    def test_key_and_type_cannot_disagree(self):
        with ShouldRaise(TypeError('type_ cannot be specified if key is a type')):
            Value(key=str, type_=int)


class TestItem:

    def test_single(self):
        h = Value(Type1)['foo']
        compare(repr(h), expected="Value(Type1)['foo']")
        check_ops(h, {'foo': 1}, expected=1)

    def test_multiple(self):
        h = Value(Type1)['foo']['bar']
        compare(repr(h), expected="Value(Type1)['foo']['bar']")
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
        compare(c.call(lambda x: x, requires(Value('key', default=1)['foo']['bar'])),
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
        compare(c.call(lambda x: x, requires(Value('key', default=1).foo.bar)),
                expected=1)


class TestCall:

    def test_resolve(self):
        context = Context()

        called = []

        def foo(bar: str):
            called.append(1)
            return bar+'b'

        def bob(x: str = Call(foo)):
            return x+'c'

        context.add('a', provides='bar')

        compare(context.call(bob), expected='abc')
        compare(context.call(bob), expected='abc')
        compare(called, expected=[1])
        compare(context.get(foo), expected='ab')

    def test_resolve_without_caching(self):
        context = Context()

        called = []

        def foo(bar: str):
            called.append(1)
            return bar+'b'

        def bob(x: str = Call(foo, cache=False)):
            return x+'c'

        context.add('a', provides='bar')

        compare(context.call(bob), expected='abc')
        compare(context.call(bob), expected='abc')
        compare(called, expected=[1, 1])
        compare(context.get(foo, default=None), expected=None)

    def test_parts_of_a_call(self):
        context = Context()

        def foo():
            return {'a': 'b'}

        def bob(x: str = Call(foo)['a']):
            return x+'c'

        compare(context.call(bob), expected='bc')


class TestAnyOf:

    def test_first(self):
        context = Context()
        context.add(('foo', ))
        context.add(('bar', ), provides=Tuple[str])

        def bob(x: str = AnyOf(tuple, Tuple[str])):
            return x[0]

        compare(context.call(bob), expected='foo')

    def test_second(self):
        context = Context()
        context.add(('bar', ), provides=Tuple[str])

        def bob(x: str = AnyOf(tuple, Tuple[str])):
            return x[0]

        compare(context.call(bob), expected='bar')

    def test_none(self):
        context = Context()

        def bob(x: str = AnyOf(tuple, Tuple[str])):
            pass

        with ShouldRaise(ResourceError):
            context.call(bob)

    def test_default(self):
        context = Context()

        def bob(x: str = AnyOf(tuple, Tuple[str], default=(42,))):
            return x[0]

        compare(context.call(bob), expected=42)


class Parent(object):
    pass


class Child(Parent):
    pass


class TestLike:

    def test_actual(self):
        context = Context()
        p = Parent()
        c = Child()
        context.add(p)
        context.add(c)

        def bob(x: str = Like(Child)):
            return x

        assert context.call(bob) is c

    def test_base(self):
        context = Context()
        p = Parent()
        context.add(p)

        def bob(x: str = Like(Child)):
            return x

        assert context.call(bob) is p

    def test_none(self):
        context = Context()
        # make sure we don't pick up object!
        context.add(object())

        def bob(x: str = Like(Child)):
            pass

        with ShouldRaise(ResourceError):
            context.call(bob)

    def test_default(self):
        context = Context()

        def bob(x: str = Like(Child, default=42)):
            return x

        compare(context.call(bob), expected=42)
