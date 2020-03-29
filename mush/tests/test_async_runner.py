import asyncio
from unittest.mock import Mock, call

import pytest
from testfixtures import compare, ShouldRaise, Comparison as C

from mush import ContextError, requires, returns
from mush.asyncio import Runner, Context
from .helpers import no_threads, must_run_in_thread


@pytest.mark.asyncio
async def test_call_is_async():
    def it():
        return 'bar'
    runner = Runner(it)
    result = runner()
    assert asyncio.iscoroutine(result)
    with must_run_in_thread(it):
        compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_resource_missing():
    def it(foo):
        pass
    runner = Runner(it)
    context = Context()
    with ShouldRaise(ContextError(C(str), runner.start, context)):
        await runner(context)


@pytest.mark.asyncio
async def test_cloned_still_async():
    def it():
        return 'bar'
    runner = Runner(it)
    runner_ = runner.clone()
    result = runner_()
    assert asyncio.iscoroutine(result)
    compare(await result, expected='bar')


@pytest.mark.asyncio
async def test_addition_still_async():
    async def foo():
        return 'foo'
    @requires(str)
    @returns()
    async def bar(foo):
        return foo+'bar'
    r1 = Runner(foo)
    r2 = Runner(bar)
    runner = r1 + r2
    result = runner()
    assert asyncio.iscoroutine(result)
    compare(await result, expected='foobar')


class CommonCM:
    m = None
    context = None
    swallow_exceptions = None


class AsyncCM(CommonCM):

    async def __aenter__(self):
        self.m.enter()
        if self.context is 'self':
            return self
        return self.context

    async def __aexit__(self, type, obj, tb):
        self.m.exit(obj)
        return self.swallow_exceptions


class SyncCM(CommonCM):

    def __enter__(self):
        self.m.enter()
        if self.context is 'self':
            return self
        return self.context

    def __exit__(self, type, obj, tb):
        self.m.exit(obj)
        return self.swallow_exceptions


def make_cm(name, type_, m, context=None, swallow_exceptions=None):
    return type(name,
                (type_,),
                {'m': getattr(m, name.lower()),
                 'context': context,
                 'swallow_exceptions': swallow_exceptions})


@pytest.mark.asyncio
async def test_async_context_manager():
    m = Mock()
    CM = make_cm('CM', AsyncCM, m)

    async def func():
        m.func()

    runner = Runner(CM, func)

    with no_threads():
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.func(),
        call.cm.exit(None)
    ])


@pytest.mark.asyncio
async def test_async_context_manager_inner_requires_cm():
    m = Mock()
    CM = make_cm('CM', AsyncCM, m, context='self')

    @requires(CM)
    async def func(obj):
        m.func(type(obj))

    runner = Runner(CM, func)

    with no_threads():
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.func(CM),
        call.cm.exit(None)
    ])


@pytest.mark.asyncio
async def test_async_context_manager_inner_requires_context():
    m = Mock()
    class CMContext: pass
    cm_context = CMContext()
    CM = make_cm('CM', AsyncCM, m, context=cm_context)

    @requires(CMContext)
    async def func(obj):
        m.func(obj)

    runner = Runner(CM, func)

    with no_threads():
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.func(cm_context),
        call.cm.exit(None)
    ])


@pytest.mark.asyncio
async def test_async_context_manager_nested():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m)
    CM2 = make_cm('CM2', AsyncCM, m)

    async def func():
        m.func()

    runner = Runner(CM1, CM2, func)

    with no_threads():
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.func(),
        call.cm2.exit(None),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_async_context_manager_nested_exception_inner_handles():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m)
    CM2 = make_cm('CM2', AsyncCM, m, swallow_exceptions=True)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    with no_threads():
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_async_context_manager_nested_exception_outer_handles():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m, swallow_exceptions=True)
    CM2 = make_cm('CM2', AsyncCM, m)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    with no_threads():
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(e),
    ])


@pytest.mark.asyncio
async def test_async_context_manager_exception_not_handled():
    m = Mock()
    CM = make_cm('CM', AsyncCM, m)

    e = Exception('foo')

    async def func():
        raise e

    runner = Runner(CM, func)

    with no_threads(), ShouldRaise(e):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.cm.exit(e)
    ])


@pytest.mark.asyncio
async def test_sync_context_manager():
    m = Mock()
    CM = make_cm('CM', SyncCM, m)

    async def func():
        m.func()

    runner = Runner(CM, func)

    with must_run_in_thread(CM.__enter__, CM.__exit__):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.func(),
        call.cm.exit(None)
    ])


@pytest.mark.asyncio
async def test_sync_context_manager_inner_requires_cm():
    m = Mock()
    CM = make_cm('CM', SyncCM, m, context='self')

    @requires(CM)
    async def func(obj):
        m.func(type(obj))

    runner = Runner(CM, func)

    with must_run_in_thread(CM.__enter__, CM.__exit__):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.func(CM),
        call.cm.exit(None)
    ])


@pytest.mark.asyncio
async def test_sync_context_manager_inner_requires_context():
    m = Mock()
    class CMContext: pass
    cm_context = CMContext()
    CM = make_cm('CM', SyncCM, m, context=cm_context)

    @requires(CMContext)
    async def func(obj):
        m.func(obj)

    runner = Runner(CM, func)

    with must_run_in_thread(CM.__enter__, CM.__exit__):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.func(cm_context),
        call.cm.exit(None)
    ])


@pytest.mark.asyncio
async def test_sync_context_manager_nested():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m)
    CM2 = make_cm('CM2', SyncCM, m)

    async def func():
        m.func()

    runner = Runner(CM1, CM2, func)

    with must_run_in_thread(CM1.__enter__, CM1.__exit__, CM2.__enter__, CM2.__exit__):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.func(),
        call.cm2.exit(None),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_sync_context_manager_nested_exception_inner_handles():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m)
    CM2 = make_cm('CM2', SyncCM, m, swallow_exceptions=True)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    with must_run_in_thread(CM1.__enter__, CM1.__exit__, CM2.__enter__, CM2.__exit__):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_sync_context_manager_nested_exception_outer_handles():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m, swallow_exceptions=True)
    CM2 = make_cm('CM2', SyncCM, m)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    with must_run_in_thread(CM1.__enter__, CM1.__exit__, CM2.__enter__, CM2.__exit__):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(e),
    ])


@pytest.mark.asyncio
async def test_sync_context_manager_exception_not_handled():
    m = Mock()
    CM = make_cm('CM', SyncCM, m)

    e = Exception('foo')

    async def func():
        raise e

    runner = Runner(CM, func)

    with must_run_in_thread(CM.__enter__, CM.__exit__), ShouldRaise(e):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm.enter(),
        call.cm.exit(e)
    ])

@pytest.mark.asyncio
async def test_sync_context_then_async_context():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m)
    CM2 = make_cm('CM2', AsyncCM, m)

    async def func():
        return 42

    runner = Runner(CM1, CM2, func)

    compare(await runner(), expected=42)

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(None),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_async_context_then_sync_context():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m)
    CM2 = make_cm('CM2', SyncCM, m)

    async def func():
        return 42

    runner = Runner(CM1, CM2, func)

    compare(await runner(), expected=42)

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(None),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_sync_context_then_async_context_exception_handled_inner():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m)
    CM2 = make_cm('CM2', AsyncCM, m, swallow_exceptions=True)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    # if something goes wrong *and handled by a CM*, you get None
    compare(await runner(), expected=None)

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_sync_context_then_async_context_exception_handled_outer():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m, swallow_exceptions=True)
    CM2 = make_cm('CM2', AsyncCM, m)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    # if something goes wrong *and handled by a CM*, you get None
    compare(await runner(), expected=None)

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(e),
    ])


@pytest.mark.asyncio
async def test_sync_context_then_async_context_exception_not_handled():
    m = Mock()
    CM1 = make_cm('CM1', SyncCM, m)
    CM2 = make_cm('CM2', AsyncCM, m)

    e = Exception('foo')

    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    with ShouldRaise(e):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(e),
    ])


@pytest.mark.asyncio
async def test_async_context_then_sync_context_exception_handled_inner():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m)
    CM2 = make_cm('CM2', SyncCM, m, swallow_exceptions=True)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    # if something goes wrong *and handled by a CM*, you get None
    compare(await runner(), expected=None)

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(None),
    ])


@pytest.mark.asyncio
async def test_async_context_then_sync_context_exception_handled_outer():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m, swallow_exceptions=True)
    CM2 = make_cm('CM2', SyncCM, m)

    e = Exception()
    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    # if something goes wrong *and handled by a CM*, you get None
    compare(await runner(), expected=None)

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(e),
    ])


@pytest.mark.asyncio
async def test_async_context_then_sync_context_exception_not_handled():
    m = Mock()
    CM1 = make_cm('CM1', AsyncCM, m)
    CM2 = make_cm('CM2', SyncCM, m)

    e = Exception('foo')

    async def func():
        raise e

    runner = Runner(CM1, CM2, func)

    with ShouldRaise(e):
        await runner()

    compare(m.mock_calls, expected=[
        call.cm1.enter(),
        call.cm2.enter(),
        call.cm2.exit(e),
        call.cm1.exit(e),
    ])
