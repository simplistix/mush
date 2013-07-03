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
