from unittest import TestCase

from mock import Mock, call
from testfixtures import ShouldRaise, StringComparison as S, compare

from mush import Periods, Runner, requires

class RunnerTests(TestCase):

    def test_simple(self):
        m = Mock()        
        def job():
            m.job()
            
        runner = Runner()
        runner.add(job)
        runner()

        compare([
                call.job()
                ], m.mock_calls)

    def test_constructor(self):
        m = Mock()        
        def job1():
            m.job1()
        def job2():
            m.job2()
            
        runner = Runner(job1, job2)
        runner()

        compare([
                call.job1(),
                call.job2(),
                ], m.mock_calls)

    def test_context_declarative(self):
        m = Mock()        
        class T1(object): pass
        class T2(object): pass

        t1 = T1()
        t2 = T2()

        def job1():
            m.job1()
            return t1

        @requires(T1)
        def job2(obj):
            m.job2(obj)
            return t2

        @requires(T2)
        def job3(obj):
            m.job3(obj)

        runner = Runner(job1, job2, job3)
        runner()
        
        compare([
                call.job1(),
                call.job2(t1),
                call.job3(t2),
                ], m.mock_calls)


    def test_context_imperative(self):
        m = Mock()        
        class T1(object): pass
        class T2(object): pass

        t1 = T1()
        t2 = T2()

        def job1():
            m.job1()
            return t1

        def job2(obj):
            m.job2(obj)
            return t2

        def job3(t2_):
            m.job3(t2_)

        # imperative config trumps declarative
        @requires(T1)
        def job4(t2_):
            m.job4(t2_)
            
        runner = Runner()
        runner.add(job1)
        runner.add(job2, T1)
        runner.add(job3, t2_=T2)
        runner.add(job4, T2)
        runner()
        
        compare([
                call.job1(),
                call.job2(t1),
                call.job3(t2),
                call.job4(t2),
                ], m.mock_calls)


    def test_returns_type_mapping(self):
        m = Mock()        
        class T1(object): pass
        class T2(object): pass
        t = T1()

        def job1():
            m.job1()
            return {T2:t}

        @requires(T2)
        def job2(obj):
            m.job2(obj)

        Runner(job1, job2)()
        
        compare([
                call.job1(),
                call.job2(t),
                ], m.mock_calls)

    def test_returns_tuple(self):
        m = Mock()        
        class T1(object): pass
        class T2(object): pass

        t1 = T1()
        t2 = T2()

        def job1():
            m.job1()
            return t1, t2

        @requires(T1, T2)
        def job2(obj1, obj2):
            m.job2(obj1, obj2)

        Runner(job1, job2)()
        
        compare([
                call.job1(),
                call.job2(t1, t2),
                ], m.mock_calls)

    def test_returns_list(self):
        m = Mock()        
        class T1(object): pass
        class T2(object): pass

        t1 = T1()
        t2 = T2()

        def job1():
            m.job1()
            return [t1, t2]

        @requires(obj1=T1, obj2=T2)
        def job2(obj1, obj2):
            m.job2(obj1, obj2)

        Runner(job1, job2)()
        
        compare([
                call.job1(),
                call.job2(t1, t2),
                ], m.mock_calls)

    def test_missing_from_context(self):
        # make sure exception is helpful
        class T(object): pass

        @requires(T)
        def job(arg):
            pass

        runner = Runner(job)
        with ShouldRaise(KeyError(
                S("'No T in context' attempting to call <function job at \w+>")
                )):
            runner()

    def test_classes(self):
        m = Mock()        
        class T0(object): pass
        class T1(object): pass
        class T2(object): pass
        t1 = T1()
        t2 = T2()
        
        class C1(object):

            def __init__(self):
                m.C1.__init__()
                             
            def meth(self):
                m.C1.method()
                return t1

            
        @requires(T1)
        class C2(object):

            def __init__(self, obj):
                m.C2.init(obj)

            @requires(T0)
            def meth1(self, obj):
                m.C2.meth1(type(obj))
                return t2

            @requires(T2)
            def meth2(self, obj):
                m.C2.meth2(obj)

        class C3(object):

            @requires(T2)
            def __call__(self, obj):
                m.C3.call(obj)

        runner = Runner(
            T0,
            C1.meth,
            C2.meth1,
            C2.meth2,
            )
        runner.add(C3.__call__)
        runner()
        
        compare([
                call.C2.init(t1),
                call.C2.meth1(T0),
                call.C2.meth2(t2),
                call.C3.call(t2),
                ], m.mock_calls)
        
        pass

    def test_clone(self):
        pass

class PeriodsTests(TestCase):

    def test_repr(self):
        p = Periods()
        compare(repr(p), '<Periods first:[] normal:[] last:[]>')
        
        p.first.append(1)
        p.normal.append(2)
        p.last.append(3)
        p.first.append(4)
        p.normal.append(5)
        p.last.append(6)
        compare(repr(p), '<Periods first:[1, 4] normal:[2, 5] last:[3, 6]>')

    def test_iter(self):
        p = Periods()
        compare(tuple(p), ())
        
        p.first.append(6)
        p.first.append(5)
        p.normal.append(4)
        p.normal.append(3)
        p.last.append(2)
        p.last.append(1)
        compare(tuple(p), (6, 5, 4, 3, 2, 1))
