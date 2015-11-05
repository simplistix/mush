from unittest import TestCase

from testfixtures import ShouldRaise

from mush.context import Context

from .compat import PY32


class TheType(object):
    def __repr__(self):
        return '<TheType obj>'


class TestContext(TestCase):

    def test_simple(self):
        obj = TheType()
        context = Context()
        context.add(obj, TheType)

        self.assertTrue(context[TheType] is obj)
        self.assertEqual(
            repr(context),
            "<Context: {<class 'mush.tests.test_context.TheType'>: <TheType obj>}>"
            )
        self.assertEqual(
            str(context),
            "<Context: {<class 'mush.tests.test_context.TheType'>: <TheType obj>}>"
            )

    def test_type_as_string(self):
        obj = TheType()
        context = Context()
        context.add(obj, type='my label')

        self.assertTrue(context['my label'] is obj)
        self.assertEqual(
            repr(context),
            "<Context: {'my label': <TheType obj>}>"
            )
        self.assertEqual(
            str(context),
            "<Context: {'my label': <TheType obj>}>"
            )

    def test_explicit_type(self):
        class T2(object): pass
        obj = TheType()
        context = Context()
        context.add(obj, T2)
        self.assertTrue(context[T2] is obj)
        if PY32:
            expected = ("<Context: {"
                        "<class 'mush.tests.test_context.TestContext."
                        "test_explicit_type.<locals>.T2'>: "
                        "<TheType obj>}>")
        else:
            expected = ("<Context: {<class 'mush.tests.test_context.T2'>:"
                        " <TheType obj>}>")
        self.assertEqual(repr(context), expected)
        self.assertEqual(str(context), expected)

    def test_clash(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, TheType)
        with ShouldRaise(ValueError('Context already contains '+repr(TheType))):
            context.add(obj2, TheType)

    def test_missing(self):
        context = Context()
        with ShouldRaise(KeyError('No '+repr(TheType)+' in context')):
            context[TheType]

    def test_clash_string_type(self):
        obj1 = TheType()
        obj2 = TheType()
        context = Context()
        context.add(obj1, type='my label')
        with ShouldRaise(ValueError("Context already contains 'my label'")):
            context.add(obj2, type='my label')

    def test_missing_string_type(self):
        context = Context()
        with ShouldRaise(KeyError("No 'my label' in context")):
            context['my label']

    def test_add_none(self):
        context = Context()
        with ShouldRaise(ValueError('Cannot add None to context')):
            context.add(None, None.__class__)

    def test_add_none_with_type(self):
        context = Context()
        context.add(None, TheType)
        self.assertTrue(context[TheType] is None)

    def test_get_none_type(self):
        self.assertTrue(Context()[type(None)] is None)

