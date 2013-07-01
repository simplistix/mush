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
        self.assertEqual(thing.context_manager, False)
        self.assertEqual(
            repr(thing),
            '<Thing (<TheType obj>): type=TheType, context_manager=False>'
            )
        self.assertEqual(
            str(thing),
            '<Thing (<TheType obj>): type=TheType, context_manager=False>'
            )
        
    def test_context_manager_auto(self):
        class MyManager(object):
            def __repr__(self):
                return '<MyManager obj>'
            def __enter__(self):
                pass
            def __exit__(self, *args):
                pass
        # check it really works as a context manager
        with MyManager():
            pass

        obj = MyManager()
        thing = Thing(obj)
        self.assertTrue(thing.it is obj)
        self.assertTrue(thing.type is MyManager)
        self.assertEqual(thing.context_manager, True)
        self.assertEqual(
            repr(thing),
            '<Thing (<MyManager obj>): type=MyManager, context_manager=True>'
            )
        self.assertEqual(
            str(thing),
            '<Thing (<MyManager obj>): type=MyManager, context_manager=True>'
            )

    def test_context_manager_explicit(self):
        class MyManager(object):
            def __repr__(self):
                return '<MyManager obj>'
            def __enter__(self):
                pass
            def __exit__(self, *args):
                pass
        # check it really works as a context manager
        with MyManager():
            pass

        obj = MyManager()
        thing = Thing(obj, context_manager=False)
        self.assertTrue(thing.it is obj)
        self.assertTrue(thing.type is MyManager)
        self.assertEqual(thing.context_manager, False)
        self.assertEqual(
            repr(thing),
            '<Thing (<MyManager obj>): type=MyManager, context_manager=False>'
            )
        self.assertEqual(
            str(thing),
            '<Thing (<MyManager obj>): type=MyManager, context_manager=False>'
            )

    def test_type_explicit(self):
        class MyType(object):
            def __repr__(self):
                return '<MyType obj>'
        obj = TheType()
        thing = Thing(obj, type=MyType)
        self.assertTrue(thing.it is obj)
        self.assertTrue(thing.type is MyType)
        self.assertEqual(thing.context_manager, False)
        self.assertEqual(
            repr(thing),
            '<Thing (<TheType obj>): type=MyType, context_manager=False>'
            )
        self.assertEqual(
            str(thing),
            '<Thing (<TheType obj>): type=MyType, context_manager=False>'
            )
