from typing import Text

from testfixtures.mock import Mock

import pytest
from testfixtures import compare, ShouldRaise

from mush import Value, missing
from mush.requirements import Requirement, AttrOp, ItemOp, AnyOf, Like, Annotation
from mush.resources import ResourceKey
from mush.tests.helpers import Type1


def check_ops(value, data, *, expected):
    for op in value.ops:
        data = op(data)
    compare(expected, actual=data)


class TestRequirement:

    def test_repr_minimal(self):
        compare(repr(Requirement((), default=missing)),
                expected="Requirement()")

    def test_repr_maximal(self):
        r = Requirement(
            keys=(
                ResourceKey(type_=str),
                ResourceKey(identifier='foo'),
                ResourceKey(type_=int, identifier='bar')
            ),
            default=None
        )
        r.ops.append(AttrOp('bar'))
        compare(repr(r),
                expected="Requirement(ResourceKey(str), ResourceKey('foo'), "
                         "ResourceKey(int, 'bar'), default=None).bar")

    special_names = ['attr', 'ops']

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

    def test_bad_type(self):
        h = Value(Type1)['foo']['bar']
        with ShouldRaise(TypeError):
            check_ops(h, [], expected=None)


class TestAttr:

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


class TestAnnotation:

    def test_name_only(self):
        r = Annotation('x', None, missing)
        compare(r.keys, expected=[
            ResourceKey(None, 'x')
        ])
        compare(r.default, expected=missing)

    def test_name_and_type(self):
        r = Annotation('x', str, missing)
        compare(r.keys, expected=[
            ResourceKey(str, 'x'),
            ResourceKey(None, 'x'),
            ResourceKey(str, None),
        ])
        compare(r.default, expected=missing)

    def test_all(self):
        r = Annotation('x', str, 'default')
        compare(r.keys, expected=[
            ResourceKey(str, 'x'),
            ResourceKey(None, 'x'),
            ResourceKey(str, None),
        ])
        compare(r.default, expected='default')

    def test_repr_min(self):
        compare(repr(Annotation('x', None, missing)),
                expected="x")

    def test_repr_max(self):
        compare(repr(Annotation('x', str, 'default')),
                expected="x: str = 'default'")


class TestValue:

    def test_type_only(self):
        v = Value(str)
        compare(v.keys, expected=[ResourceKey(str, None)])

    def test_typing_only(self):
        v = Value(Text)
        compare(v.keys, expected=[ResourceKey(Text, None)])

    def test_identifier_only(self):
        v = Value('foo')
        compare(v.keys, expected=[ResourceKey(None, 'foo')])

    def test_type_and_identifier(self):
        v = Value(str, 'foo')
        compare(v.keys, expected=[ResourceKey(str, 'foo')])

    def test_nothing_specified(self):
        with ShouldRaise(TypeError('type or identifier must be supplied')):
            Value()

    def test_repr_min(self):
        compare(repr(Value(Type1)),
                expected="Value(Type1)")

    def test_repr_max(self):
        compare(repr(Value(Type1, 'foo')['bar'].baz),
                expected="Value(Type1, 'foo')['bar'].baz")

#
# class TestAnyOf:
#
#     def test_first(self):
#         context = Context()
#         context.add(('foo', ))
#         context.add(('bar', ), provides=Tuple[str])
#
#         def bob(x: str = AnyOf(tuple, Tuple[str])):
#             return x[0]
#
#         compare(context.call(bob), expected='foo')
#
#     def test_second(self):
#         context = Context()
#         context.add(('bar', ), provides=Tuple[str])
#
#         def bob(x: str = AnyOf(tuple, Tuple[str])):
#             return x[0]
#
#         compare(context.call(bob), expected='bar')
#
#     def test_none(self):
#         context = Context()
#
#         def bob(x: str = AnyOf(tuple, Tuple[str])):
#             pass
#
#         with ShouldRaise(ResourceError):
#             context.call(bob)
#
#     def test_default(self):
#         context = Context()
#
#         def bob(x: str = AnyOf(tuple, Tuple[str], default=(42,))):
#             return x[0]
#
#         compare(context.call(bob), expected=42)
#
#
# class Parent(object):
#     pass
#
#
# class Child(Parent):
#     pass
#
#
# class TestLike:
#
#     def test_actual(self):
#         context = Context()
#         p = Parent()
#         c = Child()
#         context.add(p)
#         context.add(c)
#
#         def bob(x: str = Like(Child)):
#             return x
#
#         assert context.call(bob) is c
#
#     def test_base(self):
#         context = Context()
#         p = Parent()
#         context.add(p)
#
#         def bob(x: str = Like(Child)):
#             return x
#
#         assert context.call(bob) is p
#
#     def test_none(self):
#         context = Context()
#         # make sure we don't pick up object!
#         context.add(object())
#
#         def bob(x: str = Like(Child)):
#             pass
#
#         with ShouldRaise(ResourceError):
#             context.call(bob)
#
#     def test_default(self):
#         context = Context()
#
#         def bob(x: str = Like(Child, default=42)):
#             return x
#
#         compare(context.call(bob), expected=42)
