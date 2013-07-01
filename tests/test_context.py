from unittest import TestCase

from testfixtures import ShouldRaise

from mush import Context

class TheType(object):
    def __repr__(self):
        return '<TheType obj>'

class TestContext(TestCase):

    def test_simple(self):
        obj = TheType()
        context = Context()
        context.add(obj)

        self.assertTrue(context.get(TheType) is obj)
        self.assertEqual(
            repr(context),
            "<Context: {<class 'tests.test_context.TheType'>: <TheType obj>}>"
            )
        self.assertEqual(
            str(context),
            "<Context: {<class 'tests.test_context.TheType'>: <TheType obj>}>"
            )

    def test_explicit_type(self):
        class T2(object):
            pass
        obj = TheType()
        context = Context()
        context.add(obj, T2)
        self.assertTrue(context.get(T2) is obj)
        self.assertEqual(
            repr(context),
            "<Context: {<class 'tests.test_context.T2'>: <TheType obj>}>"
            )
        self.assertEqual(
            str(context),
            "<Context: {<class 'tests.test_context.T2'>: <TheType obj>}>"
            )

    def test_clash(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1)
        with ShouldRaise(ValueError('Context already contains TheType')):
            context.add(obj2)

    def test_missing(self):
        context = Context()
        with ShouldRaise(KeyError('No TheType in context')):
            context.get(TheType)
