from mush.context import ResolvableValue
from testfixtures import compare

from mush.markers import Marker

foo = Marker('foo')


class TestResolvableValue:

    def test_repr_with_resolver(self):
        compare(repr(ResolvableValue(None, foo)),
                expected='<Marker: foo>')
