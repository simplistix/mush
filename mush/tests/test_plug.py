from unittest import TestCase

from mock import Mock, call
from testfixtures import compare, ShouldRaise

from mush import Plug, Runner, returns, requires
from mush.tests.test_runner import verify


class TestPlug(TestCase):

    def test_simple(self):
        m = Mock()

        runner = Runner()
        runner.add(m.job1, label='one')
        runner.add(m.job2)
        runner.add(m.job3, label='three')
        runner.add(m.job4)

        class MyPlug(Plug):

            def one(self):
                m.plug_one()

            def three(self):
                m.plug_two()

        plug = MyPlug()
        plug.add_to(runner)

        runner()

        compare([
            call.job1(), call.plug_one(), call.job2(),
            call.job3(), call.plug_two(), call.job4()
        ], m.mock_calls)

        verify(runner,
               (m.job1, set()),
               (plug.one, {'one'}),
               (m.job2, set()),
               (m.job3, set()),
               (plug.three, {'three'}),
               (m.job4, set()),
               )

    def test_label_not_there(self):
        runner = Runner()

        class MyPlug(Plug):
            def not_there(self): pass

        with ShouldRaise(KeyError('not_there')):
            MyPlug().add_to(runner)

    def test_requirements_and_returns(self):
        m = Mock()

        @returns('r1')
        def job1():
            m.job1()
            return 1

        @requires('r2')
        def job3(r):
            m.job3(r)

        runner = Runner()
        runner.add(job1, label='point')
        runner.add(job3)

        class MyPlug(Plug):

            @requires('r1')
            @returns('r2')
            def point(self, r):
                m.point(r)
                return 2

        plug = MyPlug()
        plug.add_to(runner)

        runner()

        compare([
            call.job1(), call.point(1), call.job3(2),
        ], m.mock_calls)

        verify(runner,
               (job1, set()),
               (plug.point, {'point'}),
               (job3, set()),
               )
