from unittest import TestCase

from testfixtures import ShouldRaise

from mush import Context

from .compat import PY32

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
            "<Context: {<class 'mush.tests.test_context.TheType'>: <TheType obj>}>"
            )
        self.assertEqual(
            str(context),
            "<Context: {<class 'mush.tests.test_context.TheType'>: <TheType obj>}>"
            )

    def test_explicit_type(self):
        class T2(object): pass
        obj = TheType()
        context = Context()
        context.add(obj, T2)
        self.assertTrue(context.get(T2) is obj)
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
        context.add(obj1)
        with ShouldRaise(ValueError('Context already contains TheType')):
            context.add(obj2)

    def test_missing(self):
        context = Context()
        with ShouldRaise(KeyError('No TheType in context')):
            context.get(TheType)

    def test_iter(self):
        # check state is preserved
        context = Context()
        context.req_objs.append(1)
        self.assertEqual(tuple(context), (1, ))
        context.req_objs.append(2)
        self.assertEqual(tuple(context), (2, ))
        

    def test_add_none(self):
        context = Context()
        with ShouldRaise(ValueError('Cannot add None to context')):
            context.add(None)

    def test_add_none_with_type(self):
        context = Context()
        context.add(None, TheType)
        self.assertTrue(context.get(TheType) is None)

    def test_old_style_class(self):
        class Type(): pass
        obj = Type()
        context = Context()
        context.add(obj)
        self.assertTrue(context.get(Type) is obj)
        
    def test_old_style_class_explicit(self):
        class Type(): pass
        obj = object()
        context = Context()
        context.add(obj, Type)
        self.assertTrue(context.get(Type) is obj)
        
    def test_get_nonetype(self):
        self.assertTrue(Context().get(type(None)) is None)

