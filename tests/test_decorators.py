from unittest import TestCase

from testfixtures import Comparison as C, compare

from mush import Requirement, requires, requires_first, requires_last

class Type1(object): pass
class Type2(object): pass

class RequiresTests(TestCase):

    def test_simple(self):
        
        @requires(Type1)
        def job(obj):
            pass

        compare(([C(Requirement(Type1))], {}, 0),
                job.__requires__)

    def test_complex(self):
        
        @requires(Type1, k2=Type2)
        def job(obj, k1=None, k2=None):
            pass

        compare(([C(Requirement(Type1))],
                 {'k2':C(Requirement(Type2))},
                 0),
                job.__requires__)

    def test_no_molestation(self):
        def job(arg): pass
        decorated = requires(Type1)(job)
        self.assertTrue(decorated is job)

    def test_requires_last(self):
        @requires_first(Type1)
        def job(a):
            pass
        compare(([C(Requirement(Type1))], {}, -1),
                job.__requires__)

    def test_requires_first(self):
        @requires_last(Type1)
        def job(a):
            pass
        compare(([C(Requirement(Type1))], {}, 1),
                job.__requires__)
