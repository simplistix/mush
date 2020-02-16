from testfixtures import compare

from mush import returns
from mush.resolvers import Factory, ValueResolver
from mush.markers import Marker

foo = Marker('foo')


class TestValueResolver:

    def test_repr(self):
        f = ValueResolver(foo)
        compare(repr(f), expected='<Marker: foo>')


class TestFactory:

    def test_repr(self):
        f = Factory(foo, None, returns('foo'))
        compare(repr(f), expected='<Factory for <Marker: foo>>')
