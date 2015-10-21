from unittest import TestCase
from testfixtures import compare
from mush import marker


class TestMarkers(TestCase):

    def test_repr(self):
        compare(repr(marker('SetupComplete')), '<Marker: SetupComplete>')

    def test_multiple_calls(self):
        m1 = marker('SetupComplete')
        m2 = marker('SetupComplete')
        self.assertTrue(m1 is m2)
