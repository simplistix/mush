from unittest import TestCase

from testfixtures import ShouldRaise, compare

from mush import requires, first, last, when

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
    def test_when_not_type(self):
        obj = Type1()
        w = when(obj)
        with ShouldRaise(AttributeError(
                "'Type1' object has no attribute '__name__'"
                )):
            repr(w)

    def test_first(self):
        f = first(Type1)
        compare(repr(f), 'first(Type1)')
        compare(f.type, Type1)
        self.assertTrue(isinstance(f, when))

    def test_last(self):
        l = last(Type1)
        compare(repr(l), 'last(Type1)')
        compare(l.type, Type1)
        self.assertTrue(isinstance(l, when))
