from unittest import TestCase

from testfixtures import ShouldRaise

from mush import Context, Thing
from .test_thing import TheType

class TestThing(TestCase):

    def test_simple(self):
        obj = TheType()
        context = Context()
        context.add(Thing(obj))

        self.assertTrue(context.get(TheType) is obj)
        self.assertEqual(
            repr(context),
            '<Context: '
            '(<Thing (<TheType obj>): type=TheType>)>'
            )
        self.assertEqual(
            str(context),
            '<Context: '
            '(<Thing (<TheType obj>): type=TheType>)>'
            )
        
    def test_clash(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(Thing(obj1))
        with ShouldRaise(ValueError('Context already contains TheType')):
            context.add(Thing(obj2))

    def test_wrong_type(self):
        context = Context()
        with ShouldRaise(TypeError('Can only add Thing instances to Contexts')):
            context.add(TheType())

    def test_missing(self):
        context = Context()
        with ShouldRaise(KeyError('No TheType in context')):
            context.get(TheType)
