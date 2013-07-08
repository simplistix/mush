from unittest import TestCase

from testfixtures import ShouldRaise, compare

from mush import Requirements, requires, first, last, when

class Type1(object): pass
class Type2(object): pass

class RequiresTests(TestCase):

    def test_simple(self):
        
        @requires(Type1)
        def job(obj):
            pass # pragma: nocover

        compare(((None, Type1), ),
                tuple(job.__requires__))

    def test_complex(self):
        
        @requires(Type1, k2=Type2)
        def job(obj, k1=None, k2=None):
            pass # pragma: nocover

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

    def test_when_default(self):
        w = when()
        self.assertTrue(w.type is type(None))

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

class RequirementsTests(TestCase):

    def test_repr_empty(self):
        compare(repr(Requirements()), 'Requirements()')

    def test_repr_args(self):
        compare(repr(Requirements(Type1, Type2)),
                'Requirements(Type1, Type2)')

    def test_repr_kw(self):
        compare(repr(Requirements(x=Type1, y=Type2)),
                'Requirements(x=Type1, y=Type2)')

    def test_repr_both(self):
        compare(repr(Requirements(Type1, y=Type2)),
                'Requirements(Type1, y=Type2)')

    def test_iter_empty(self):
        compare((), tuple(Requirements()))

    def test_iter_args(self):
        compare(((None, Type1), (None, Type2)),
                tuple(Requirements(Type1, Type2)))

    def test_iter_kw(self):
        compare([('x', Type1), ('y', Type2)],
                sorted(Requirements(x=Type1, y=Type2)))

    def test_iter_both(self):
        compare(((None, Type1), ('x', Type2)),
                tuple(Requirements(Type1, x=Type2)))
