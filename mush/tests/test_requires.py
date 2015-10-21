from unittest import TestCase

from testfixtures import ShouldRaise, compare

from mush import (
    Requirements, requires,
    first, last, when,
    item, attr, how,
    after
    )

class Type1(object): pass
class Type2(object): pass
class Type3(object): pass

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

    def test_stacking(self):
        
        @requires(Type2, k2=Type1)
        @requires(Type1, k1=Type2)
        def job(obj1, obj2, k1=None, k2=None):
            pass # pragma: nocover

        args = [t for t in job.__requires__ if t[0] is None]
        kw = set(t for t in job.__requires__ if t[0] is not None)
        
        compare([(None, Type1), (None, Type2)], args)
        compare(set((('k1', Type2), ('k2', Type1))), kw)
        
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

    def test_item(self):
        o = item(Type1, 'the key')
        compare(repr(o), "Type1['the key']")
        compare(o.type, Type1)
        compare(o.names, ('the key', ))
        self.assertTrue(isinstance(o, how))

    def test_attr(self):
        o = attr(Type1, 'the secret')
        compare(repr(o), "Type1.the secret")
        compare(o.type, Type1)
        compare(o.names, ('the secret', ))
        self.assertTrue(isinstance(o, how))
    
    def test_when_how(self):
        w = first(attr(Type1, 'foo'))
        compare(repr(w), 'first(Type1.foo)')
        self.assertTrue(isinstance(w, when))
        h = w.type
        compare(h.type, Type1)
        compare(h.names, ('foo', ))
        self.assertTrue(isinstance(h, how))
    
    def test_how_when(self):
        h = attr(first(Type1), 'foo')
        compare(repr(h), 'first(Type1).foo')
        compare(h.names, ('foo',), )
        self.assertTrue(isinstance(h, how))
        w = h.type
        self.assertTrue(isinstance(w, when))
        compare(w.type, Type1)

    def test_after(self):
        w = after(Type1)
        compare(repr(w), 'last(ignore(Type1))')
        self.assertTrue(isinstance(w, when))
        h = w.type
        compare(h.type, Type1)
        compare(h.names, ())
        self.assertTrue(isinstance(h, how))
    
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

    def test_repr_all(self):
        requirements = Requirements(Type1, y=Type2)
        requirements.returns = Type3
        compare(repr(requirements),
                'Requirements(Type1, y=Type2) -> Type3')

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
