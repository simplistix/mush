from testfixtures import compare

from mush import returns
from mush.factory import Factory
from mush.markers import Marker

foo = Marker('foo')


def test_repr():
    f = Factory(foo, None, returns('foo'))
    compare(repr(f), expected='<Factory for <Marker: foo>>')
