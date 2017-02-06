from unittest import TestCase

from mock import Mock, call
from testfixtures import (
    ShouldRaise,
    compare
    )

from mush.context import ContextError
from mush.declarations import (
    requires, attr, item, nothing, returns, returns_mapping)
from mush.runner import Runner
from .compat import PY2


def verify(runner, *expected):
    seen_labels = set()

    actual = []
    point = runner.start
    while point:
        actual.append((point.obj, point.labels))
        for label in point.labels:
            if label in seen_labels: # pragma: no cover
                raise AssertionError('%s occurs more than once' % label)
            seen_labels.add(label)
            compare(runner.labels[label], point)
        point = point.next

    compare(expected=expected, actual=actual)

    actual_reverse = []
    point = runner.end
    while point:
        actual_reverse.append((point.obj, point.labels))
        point = point.previous

    compare(actual, reversed(actual_reverse))
    compare(seen_labels, runner.labels.keys())


class RunnerTests(TestCase):

    def test_simple(self):
        m = Mock()
        def job():
            m.job()

        runner = Runner()
        point = runner.add(job).callpoint

        compare(job, point.obj)
        compare(runner.start, point)
        compare(runner.end, point)
        runner()

        compare([
                call.job()
                ], m.mock_calls)

        verify(runner, (job, set()))

    def test_constructor(self):
        m = Mock()
        def job1():
            m.job1()
        def job2():
            m.job2()

        runner = Runner(job1, job2)
        compare(job1, runner.start.obj)
        compare(job2, runner.end.obj)

        runner()

        compare([
                call.job1(),
                call.job2(),
                ], m.mock_calls)

        verify(runner,
                    (job1, set()),
                    (job2, set()))

    def test_return_value(self):
        def job():
            return 42
        runner = Runner(job)
        compare(runner(), 42)

    def test_return_value_empty(self):
        runner = Runner()
        compare(runner(), None)

    def test_add_with_label(self):
        def job1(): pass
        def job2(): pass

        runner = Runner()

        point1 = runner.add(job1, label='1').callpoint
        point2 = runner.add(job2, label='2').callpoint

        compare(point1.obj, job1)
        compare(point2.obj, job2)

        compare(runner['1'].callpoint, point1)
        compare(runner['2'].callpoint, point2)

        compare({'1'}, point1.labels)
        compare({'2'}, point2.labels)

        verify(runner,
                    (job1, {'1'}),
                    (job2, {'2'}))

    def test_modifier_add_moves_label(self):
        def job1(): pass
        def job2(): pass

        runner = Runner()

        runner.add(job1, label='the label')
        runner['the label'].add(job2)

        verify(runner,
                    (job1, set()),
                    (job2, {'the label'}))

    def test_runner_add_does_not_move_label(self):
        def job1(): pass
        def job2(): pass

        runner = Runner()

        runner.add(job1, label='the label')
        runner.add(job2)

        verify(runner,
                    (job1, {'the label'}),
                    (job2, set()))

    def test_modifier_moves_only_explicit_label(self):
        def job1(): pass
        def job2(): pass

        runner = Runner()

        mod = runner.add(job1)
        mod.add_label('1')
        mod.add_label('2')

        verify(runner,
                    (job1, {'1', '2'}))

        runner['2'].add(job2)

        verify(runner,
                    (job1, {'1'}),
                    (job2, {'2'}))

    def test_modifier_add_with_label(self):
        def job1(): pass
        def job2(): pass

        runner = Runner()

        mod = runner.add(job1)
        mod.add_label('1')

        runner['1'].add(job2, label='2')

        verify(runner,
                    (job1, {'1'}),
                    (job2, {'2'}))

    def test_runner_add_label(self):
        m = Mock()

        runner = Runner()
        runner.add(m.job1)
        runner.add_label('label')
        runner.add(m.job3)

        runner['label'].add(m.job2)

        verify(
            runner,
            (m.job1, set()),
            (m.job2, {'label'}),
            (m.job3, set())
        )

        cloned = runner.clone(added_using='label')
        verify(
            cloned,
            (m.job2, {'label'}),
        )

    def test_declarative(self):
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

    def test_imperative(self):
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
        runner.add(job2, requires(T1))
        runner.add(job3, requires(t2_=T2))
        runner.add(job4, requires(T2))
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

        @returns_mapping()
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

    def test_returns_type_mapping_of_none(self):
        m = Mock()
        class T2(object): pass

        @returns_mapping()
        def job1():
            m.job1()
            return {T2:None}

        @requires(T2)
        def job2(obj):
            m.job2(obj)

        Runner(job1, job2)()

        compare([
                call.job1(),
                call.job2(None),
                ], m.mock_calls)

    def test_returns_tuple(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass

        t1 = T1()
        t2 = T2()

        @returns(T1, T2)
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

        runner = Runner()
        runner.add(job1, returns=returns(T1, T2))
        runner.add(job2)
        runner()

        compare([
                call.job1(),
                call.job2(t1, t2),
                ], m.mock_calls)

    def test_return_type_specified_decorator(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass
        t = T1()

        @returns(T2)
        def job1():
            m.job1()
            return t

        @requires(T2)
        def job2(obj):
            m.job2(obj)

        Runner(job1, job2)()

        compare([
                call.job1(),
                call.job2(t),
                ], m.mock_calls)

    def test_return_type_specified_imperative(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass
        t = T1()

        def job1():
            m.job1()
            return t

        @requires(T2)
        def job2(obj):
            m.job2(obj)

        runner = Runner()
        runner.add(job1, returns=returns(T2))
        runner.add(job2, requires(T2))
        runner()

        compare([
                call.job1(),
                call.job2(t),
                ], m.mock_calls)

    def test_missing_from_context_no_chain(self):
        class T(object): pass

        @requires(T)
        def job(arg):
            pass # pragma: nocover

        runner = Runner(job)

        with ShouldRaise(ContextError) as s:
            runner()

        text = '\n'.join((
            'While calling: '+repr(job)+' requires(T) returns_result_type()',
            'with <Context: {}>:',
            '',
            'No '+repr(T)+' in context',
        ))
        compare(text, repr(s.raised))
        compare(text, str(s.raised))

    def test_missing_from_context_with_chain(self):
        class T(object): pass

        def job1(): pass
        def job2(): pass

        @requires(T)
        def job3(arg):
            pass # pragma: nocover

        def job4(): pass
        def job5(): pass

        runner = Runner()
        runner.add(job1, label='1')
        runner.add(job2)
        runner.add(job3)
        runner.add(job4, label='4')
        runner.add(job5, requires('foo', bar='baz'), returns('bob'))

        with ShouldRaise(ContextError) as s:
            runner()

        text = '\n'.join((
            '',
            '',
            'Already called:',
            repr(job1)+' requires() returns_result_type() <-- 1',
            repr(job2)+' requires() returns_result_type()',
            '',
            'While calling: '+repr(job3)+' requires(T) returns_result_type()',
            'with <Context: {}>:',
            '',
            'No '+repr(T)+' in context',
            '',
            'Still to call:',
            repr(job4)+' requires() returns_result_type() <-- 4',
            repr(job5)+" requires('foo', bar='baz') returns('bob')",
        ))
        compare(text, repr(s.raised))
        compare(text, str(s.raised))

    def test_job_called_badly(self):
        def job(arg):
            pass # pragma: nocover
        runner = Runner(job)
        with ShouldRaise(TypeError) as s:
            runner()

        if PY2:
            message = "job() takes exactly 1 argument (0 given)"
        else:
            message = "job() missing 1 required positional argument: 'arg'"

        compare(message, actual=str(s.raised))

    def test_already_in_context(self):
        class T(object): pass

        t1 = T()

        @returns(T, T)
        def job():
            return t1, T()

        runner = Runner(job)

        with ShouldRaise(ContextError) as s:
            runner()

        text = '\n'.join((
            'While calling: '+repr(job)+' requires() returns(T, T)',
            'with <Context: {\n'
            '    '+repr(T)+': '+repr(t1)+'\n'
            '}>:',
            '',
            'Context already contains '+repr(T),
        ))
        compare(text, repr(s.raised))
        compare(text, str(s.raised))

    def test_job_error(self):
        def job():
            raise Exception('huh?')
        runner = Runner(job)
        with ShouldRaise(Exception('huh?')):
            runner()

    def test_attr(self):
        class T(object):
            foo = 'bar'
        m = Mock()
        def job1():
            m.job1()
            return T()
        def job2(obj):
            m.job2(obj)
        runner = Runner()
        runner.add(job1)
        runner.add(job2, requires(attr(T, 'foo')))
        runner()

        compare([
                call.job1(),
                call.job2('bar'),
                ], m.mock_calls)

    def test_attr_multiple(self):
        class T2:
            bar = 'baz'
        class T:
            foo = T2()

        m = Mock()
        def job1():
            m.job1()
            return T()
        def job2(obj):
            m.job2(obj)
        runner = Runner()
        runner.add(job1)
        runner.add(job2, requires(attr(T, 'foo', 'bar')))
        runner()

        compare([
                call.job1(),
                call.job2('baz'),
                ], m.mock_calls)

    def test_item(self):
        class MyDict(dict): pass
        m = Mock()
        def job1():
            m.job1()
            obj = MyDict()
            obj['the_thing'] = m.the_thing
            return obj
        def job2(obj):
            m.job2(obj)
        runner = Runner()
        runner.add(job1)
        runner.add(job2, requires(item(MyDict, 'the_thing')))
        runner()
        compare([
                call.job1(),
                call.job2(m.the_thing),
                ], m.mock_calls)

    def test_item_multiple(self):
        class MyDict(dict): pass
        m = Mock()
        def job1():
            m.job1()
            obj = MyDict()
            obj['the_thing'] = dict(other_thing=m.the_thing)
            return obj
        def job2(obj):
            m.job2(obj)
        runner = Runner()
        runner.add(job1)
        runner.add(job2, requires(item(MyDict, 'the_thing', 'other_thing')))
        runner()
        compare([
                call.job1(),
                call.job2(m.the_thing),
                ], m.mock_calls)

    def test_nested(self):
        class T(object):
            foo = dict(baz='bar')
        m = Mock()
        def job1():
            m.job1()
            return T()
        def job2(obj):
            m.job2(obj)
        runner = Runner()
        runner.add(job1)
        runner.add(job2, requires(item(attr(T, 'foo'), 'baz')))
        runner()

        compare([
                call.job1(),
                call.job2('bar'),
                ], m.mock_calls)

    def test_context_manager(self):
        m = Mock()

        class CM1(object):
            def __enter__(self):
                m.cm1.enter()
                return self
            def __exit__(self, type, obj, tb):
                m.cm1.exit(type, obj)
                return True

        class CM2Context(object): pass

        class CM2(object):
            def __enter__(self):
                m.cm2.enter()
                return CM2Context()

            def __exit__(self, type, obj, tb):
                m.cm2.exit(type, obj)

        @requires(CM1)
        def func1(obj):
            m.func1(type(obj))

        @requires(CM1, CM2, CM2Context)
        def func2(obj1, obj2, obj3):
            m.func2(type(obj1),
                    type(obj2),
                    type(obj3))
            return '2'

        runner = Runner(
            CM1,
            CM2,
            func1,
            func2,
            )

        result = runner()
        compare(result, '2')

        compare([
                call.cm1.enter(),
                call.cm2.enter(),
                call.func1(CM1),
                call.func2(CM1, CM2, CM2Context),
                call.cm2.exit(None, None),
                call.cm1.exit(None, None)
                ], m.mock_calls)

        # now check with an exception
        m.reset_mock()
        m.func2.side_effect = e = Exception()
        result = runner()

        # if something goes wrong, you get None
        compare(None, result)

        compare([
                call.cm1.enter(),
                call.cm2.enter(),
                call.func1(CM1),
                call.func2(CM1, CM2, CM2Context),
                call.cm2.exit(Exception, e),
                call.cm1.exit(Exception, e)
                ], m.mock_calls)

    def test_marker_interfaces(self):
        # return {Type:None}
        # don't pass when a requirement is for a type but value is None
        class Marker(object): pass

        m = Mock()

        def setup():
            m.setup()
            return {Marker: nothing}

        @requires(Marker)
        def use():
            m.use()

        runner = Runner()
        runner.add(setup, returns=returns_mapping(), label='setup')
        runner['setup'].add(use)
        runner()

        compare([
                call.setup(),
                call.use(),
                ], m.mock_calls)

    def test_clone(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass
        def f1(): m.f1()
        def n1():
            m.n1()
            return T1(), T2()
        def l1(): m.l1()
        def t1(obj): m.t1()
        def t2(obj): m.t2()
        # original
        runner1 = Runner()
        runner1.add(f1, label='first')
        runner1.add(n1, returns=returns(T1, T2), label='normal')
        runner1.add(l1, label='last')
        runner1.add(t1, requires(T1))
        runner1.add(t2, requires(T2))
        # now clone and add bits
        def f2(): m.f2()
        def n2(): m.n2()
        def l2(): m.l2()
        def tn(obj): m.tn()
        runner2 = runner1.clone()
        runner2['first'].add(f2)
        runner2['normal'].add(n2)
        runner2['last'].add(l2)
        # make sure types stay in order
        runner2.add(tn, requires(T2))

        # now run both, and make sure we only get what we should

        runner1()
        verify(runner1,
                    (f1, {'first'}),
                    (n1, {'normal'}),
                    (l1, {'last'}),
                    (t1, set()),
                    (t2, set()),
                    )
        compare([
                call.f1(),
                call.n1(),
                call.l1(),
                call.t1(),
                call.t2(),
                ], m.mock_calls)

        m.reset_mock()

        runner2()
        verify(runner2,
                    (f1, set()),
                    (f2, {'first'}),
                    (n1, set()),
                    (n2, {'normal'}),
                    (l1, set()),
                    (l2, {'last'}),
                    (t1, set()),
                    (t2, set()),
                    (tn, set()),
                    )
        compare([
                call.f1(),
                call.f2(),
                call.n1(),
                call.n2(),
                call.l1(),
                call.l2(),
                call.t1(),
                call.t2(),
                call.tn()
                ], m.mock_calls)

    def test_clone_end_label(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')
        runner1.add(m.f3, label='third')

        runner2 = runner1.clone(end_label='third')
        verify(runner2,
                    (m.f1, {'first'}),
                    (m.f2, {'second'}),
                    )

    def test_clone_end_label_include(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')
        runner1.add(m.f3, label='third')

        runner2 = runner1.clone(end_label='second', include_end=True)
        verify(runner2,
                    (m.f1, {'first'}),
                    (m.f2, {'second'}),
                    )

    def test_clone_start_label(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')
        runner1.add(m.f3, label='third')

        runner2 = runner1.clone(start_label='first')
        verify(runner2,
                    (m.f2, {'second'}),
                    (m.f3, {'third'}),
                    )

    def test_clone_start_label_include(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')
        runner1.add(m.f3, label='third')

        runner2 = runner1.clone(start_label='second', include_start=True)
        verify(runner2,
                    (m.f2, {'second'}),
                    (m.f3, {'third'}),
                    )

    def test_clone_between(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')
        runner1.add(m.f3, label='third')
        runner1.add(m.f4, label='fourth')

        runner2 = runner1.clone(start_label='first', end_label='fourth')
        verify(runner2,
                    (m.f2, {'second'}),
                    (m.f3, {'third'}),
                    )

    def test_clone_between_one_item(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')
        runner1.add(m.f3, label='third')

        runner2 = runner1.clone(start_label='first', end_label='third')
        verify(runner2,
                    (m.f2, {'second'}),
                    )

    def test_clone_between_empty(self):
        m = Mock()
        runner1 = Runner()
        runner1.add(m.f1, label='first')
        runner1.add(m.f2, label='second')

        runner2 = runner1.clone(start_label='first', end_label='second')
        verify(runner2)

    def test_clone_added_using(self):
        runner1 = Runner()
        m = Mock()
        runner1.add(m.f1)
        runner1.add(m.f2, label='the_label')
        runner1.add(m.f3)

        runner1['the_label'].add(m.f6)
        runner1['the_label'].add(m.f7)

        runner2 = runner1.clone(added_using='the_label')
        verify(runner2,
               (m.f6, set()),
               (m.f7, {'the_label'}),
               )

    def test_extend(self):
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

        runner = Runner()
        runner.extend(job1, job2, job3)
        runner()

        compare([
                call.job1(),
                call.job2(t1),
                call.job3(t2),
                ], m.mock_calls)

    def test_addition(self):
        m = Mock()

        def job1():
            m.job1()

        def job2():
            m.job2()

        def job3():
            m.job3()

        runner1 = Runner(job1, job2)
        runner2 = Runner(job3)
        runner = runner1 + runner2
        runner()

        verify(runner,
                    (job1, set()),
                    (job2, set()),
                    (job3, set()),
                    )
        compare([
                call.job1(),
                call.job2(),
                call.job3(),
                ], m.mock_calls)

    def test_extend_with_runners(self):
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

        runner1 = Runner(job1)
        runner2 = Runner(job2)
        runner3 = Runner(job3)

        runner = Runner(runner1)
        runner.extend(runner2, runner3)
        runner()

        verify(runner,
                    (job1, set()),
                    (job2, set()),
                    (job3, set()),
                    )
        compare([
                call.job1(),
                call.job2(t1),
                call.job3(t2),
                ], m.mock_calls)

    def test_replace_for_testing(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass

        t1 = T1()
        t2 = T2()

        def job1():
            raise Exception() # pragma: nocover

        @requires(T1)
        def job2(obj):
            raise Exception() # pragma: nocover

        @requires(T2)
        def job3(obj):
            raise Exception() # pragma: nocover

        runner = Runner(job1, job2, job3)
        runner.replace(job1, m.job1)
        m.job1.return_value = t1
        runner.replace(job2, m.job2)
        m.job2.return_value = t2
        runner.replace(job3, m.job3)
        runner()

        compare([
                call.job1(),
                call.job2(t1),
                call.job3(t2),
                ], m.mock_calls)

    def test_replace_for_behaviour(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass
        class T3(object): pass
        class T4(object): pass

        t2 = T2()
        def job0():
            return t2

        @requires(T1)
        @returns(T3)
        def job1(obj):
            raise Exception() # pragma: nocover

        job2 = requires(T4)(m.job2)
        runner = Runner(job0, job1, job2)

        runner.replace(job1, requires(T2)(returns(T4)(m.job1)))
        runner()

        compare([
            call.job1(t2),
            call.job2(m.job1.return_value),
        ], actual=m.mock_calls)

    def test_replace_explicit_requires_returns(self):
        m = Mock()
        class T1(object): pass
        class T2(object): pass
        class T3(object): pass
        class T4(object): pass

        t2 = T2()
        def job0():
            return t2

        @requires(T1)
        @returns(T3)
        def job1(obj):
            raise Exception() # pragma: nocover

        job2 = requires(T4)(m.job2)
        runner = Runner(job0, job1, job2)

        runner.replace(job1, m.job1, requires=T2, returns=T4)
        runner()

        compare([
            call.job1(t2),
            call.job2(m.job1.return_value),
        ], actual=m.mock_calls)

    def test_replace_explicit_with_labels(self):
        m = Mock()

        runner = Runner(m.job0)
        runner.add_label('foo')
        runner['foo'].add(m.job1)
        runner['foo'].add(m.job2)

        runner.replace(m.job2, m.jobnew, returns='mock')

        runner()

        compare([
            call.job0(),
            call.job1(),
            call.jobnew()
        ], m.mock_calls)

        # check added_using is handled correctly
        m.reset_mock()
        runner2 = runner.clone(added_using='foo')
        runner2()

        compare([
            call.job1(),
            call.jobnew()
        ], actual=m.mock_calls)

        # check runner's label pointer is sane
        m.reset_mock()
        runner['foo'].add(m.job3)
        runner()

        compare([
            call.job0(),
            call.job1(),
            call.jobnew(),
            call.job3()
        ], actual=m.mock_calls)

    def test_replace_explicit_at_start(self):
        m = Mock()
        runner = Runner(m.job1, m.job2)

        runner.replace(m.job1, m.jobnew, returns='mock')
        runner()

        compare([
            call.jobnew(),
            call.job2(),
        ], actual=m.mock_calls)

    def test_replace_explicit_at_end(self):
        m = Mock()
        runner = Runner(m.job1, m.job2)

        runner.replace(m.job2, m.jobnew, returns='mock')
        runner.add(m.jobnew2)
        runner()

        compare([
            call.job1(),
            call.jobnew(),
            call.jobnew2(),
        ], actual=m.mock_calls)

    def test_modifier_changes_endpoint(self):
        m = Mock()
        runner = Runner(m.job1)
        compare(runner.end.obj, m.job1)
        verify(runner,
                    (m.job1, set()),
                    )

        mod = runner.add(m.job2, label='foo')
        compare(runner.end.obj, m.job2)
        verify(runner,
                    (m.job1, set()),
                    (m.job2, {'foo'}),
                    )

        mod.add(m.job3)
        compare(runner.end.obj, m.job3)
        compare(runner.end.labels, {'foo'})
        verify(runner,
                    (m.job1, set()),
                    (m.job2, set()),
                    (m.job3, {'foo'}),
                    )

        runner.add(m.job4)
        compare(runner.end.obj, m.job4)
        compare(runner.end.labels, set())
        verify(runner,
                    (m.job1, set()),
                    (m.job2, set()),
                    (m.job3, {'foo'}),
                    (m.job4, set()),
                    )

    def test_duplicate_label_runner_add(self):
        m = Mock()
        runner = Runner()
        runner.add(m.job1, label='label')
        runner.add(m.job2)
        with ShouldRaise(ValueError(
            "'label' already points to "+repr(m.job1)+" requires() "
            "returns_result_type() <-- label"
        )):
            runner.add(m.job3, label='label')
        verify(runner,
                    (m.job1, {'label'}),
                    (m.job2, set()),
                    )

    def test_duplicate_label_runner_next_add(self):
        m = Mock()
        runner = Runner()
        runner.add(m.job1, label='label')
        with ShouldRaise(ValueError(
            "'label' already points to "+repr(m.job1)+" requires() "
            "returns_result_type() <-- label"
        )):
            runner.add(m.job2, label='label')
        verify(runner,
                    (m.job1, {'label'}),
                    )

    def test_duplicate_label_modifier(self):
        m = Mock()
        runner = Runner()
        runner.add(m.job1, label='label1')
        mod = runner['label1']
        mod.add(m.job2, label='label2')
        with ShouldRaise(ValueError(
            "'label1' already points to "+repr(m.job1)+" requires() "
            "returns_result_type() <-- label1"
        )):
            mod.add(m.job3, label='label1')
        verify(runner,
                    (m.job1, {'label1'}),
                    (m.job2, {'label2'}),
                    )

    def test_repr(self):
        class T1: pass
        class T2: pass
        m = Mock()
        runner = Runner()
        runner.add(m.job1, label='label1')
        runner.add(m.job2, requires('foo', T1), returns(T2), label='label2')
        runner.add(m.job3)

        compare('\n'.join((
            '<Runner>',
            '    '+repr(m.job1)+' requires() returns_result_type() <-- label1',
            '    '+repr(m.job2)+" requires('foo', T1) returns(T2) <-- label2",
            '    '+repr(m.job3)+' requires() returns_result_type()',
            '</Runner>'

        )), repr(runner))

    def test_repr_empty(self):
        compare('<Runner></Runner>', repr(Runner()))
