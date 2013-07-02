from unittest import TestCase

from testfixtures import compare

from mush import requires

class Type1(object): pass
class Type2(object): pass

class RequiresTests(TestCase):

    def test_simple(self):
        
        @requires(Type1)
        def job(obj):
            pass

        compare(((None, Type1), ),
                tuple(job.__requires__))

    def test_complex(self):
        
        @requires(Type1, k2=Type2)
        def job(obj, k1=None, k2=None):
            pass

        compare(((None, Type1), ('k2', Type2)),
                tuple(job.__requires__))

    def test_no_molestation(self):
        def job(arg): pass
        decorated = requires(Type1)(job)
        self.assertTrue(decorated is job)
