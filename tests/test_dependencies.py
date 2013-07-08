from unittest import TestCase

from mock import Mock, call
from testfixtures import ShouldRaise, StringComparison as S, compare

from mush import Runner, requires, first, last

class RunnerTests(TestCase):

    def test_simple_chain(self):
        m = Mock()        
        class T1(object): pass
        class T2(object): pass
        t1 = T1()
        t2 = T2()
        
        def parser():
            m.parser()
            return t1

        @requires(T1)
        def base_args(obj):
            m.base_args(obj)

        @requires(last(T1))
        def parse(obj):
            m.parse(obj)
            return t2

        runner = Runner(parser, base_args, parse)
        
        @requires(T1)
        def my_args(obj):
            m.my_args(obj)

        runner.add(my_args)
        
        @requires(T2)
        def job(obj):
            m.job(obj)

        runner.add(job)

        runner()
        
        compare([
                call.parser(),
                call.base_args(t1),
                call.my_args(t1),
                call.parse(t1),
                call.job(t2),
                ], m.mock_calls)

    def test_circular(self):
        pass

    def test_complex_(self):
        # parser -> args -> dbs (later) -> job (earlier)
        pass

    def test_ordering(self):
        m = Mock()
        class Type(): pass

        @requires(first())
        def f_none(): m.f_none()
        def n_none(): m.n_none()
        @requires(last())
        def l_none(): m.l_none()
        def make_t(): return Type()

        @requires(first(Type))
        def f_t(t): m.f_t()
        @requires(Type)
        def n_t(t): m.n_t()
        @requires(last(Type))
        def l_t(t): m.l_t()
        
        Runner(l_t, n_t, l_none, f_t, f_none, n_none, make_t)()
        
        compare([
                call.f_none(),
                call.n_none(),
                call.l_none(),
                call.f_t(),
                call.n_t(),
                call.l_t(),
                ], m.mock_calls)
