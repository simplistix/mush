from mush.context import ResolvableValue
from testfixtures import compare

from mush import returns
from mush.resolvers import Lazy
from mush.markers import Marker

foo = Marker('foo')


class TestLazy:

    def test_repr(self):
        f = Lazy(foo, None, returns('foo'))
        compare(repr(f), expected='<Lazy for <Marker: foo>>')


class TestResolvableValue:

    def test_repr_with_resolver(self):
        compare(repr(ResolvableValue(None, foo)),
                expected='<Marker: foo>')
