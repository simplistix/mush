from unittest import TestCase

from mush import Thing

class TheType(object):
    def __repr__(self):
        return '<TheType obj>'
    
class TestThing(TestCase):

    def test_simple(self):
        obj = TheType()
        thing = Thing(obj)
        self.assertTrue(thing.it is obj)
        self.assertTrue(thing.type is TheType)
        self.assertEqual(
            repr(thing),
            '<Thing (<TheType obj>): type=TheType>'
            )
        self.assertEqual(
            str(thing),
            '<Thing (<TheType obj>): type=TheType>'
            )
        
    def test_type_explicit(self):
        class MyType(object):
            def __repr__(self):
                return '<MyType obj>'
        obj = TheType()
        thing = Thing(obj, type=MyType)
        self.assertTrue(thing.it is obj)
        self.assertTrue(thing.type is MyType)
        self.assertEqual(
            repr(thing),
            '<Thing (<TheType obj>): type=MyType>'
            )
        self.assertEqual(
            str(thing),
            '<Thing (<TheType obj>): type=MyType>'
            )
