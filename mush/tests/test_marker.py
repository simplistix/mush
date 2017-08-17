from mush.markers import Marker
from testfixtures import compare


def test_repr():
    compare(repr(Marker('foo')), expected='<Marker: foo>')
