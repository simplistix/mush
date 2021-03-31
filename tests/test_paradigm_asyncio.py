import asyncio
from contextlib import contextmanager
from functools import partial
from unittest.mock import Mock

import pytest
from testfixtures import compare

from mush import Context
from mush.paradigms import Call
from mush import paradigms
from mush.paradigms.asyncio_ import AsyncIO


@contextmanager
def no_threads():
    loop = asyncio.get_event_loop()
    original = loop.run_in_executor
    loop.run_in_executor = Mock(side_effect=Exception('threads used when they should not be'))
    try:
        yield
    finally:
        loop.run_in_executor = original


@contextmanager
def must_run_in_thread(*expected):
    seen = set()
    loop = asyncio.get_event_loop()
    original = loop.run_in_executor

    def recording_run_in_executor(executor, func, *args):
        if isinstance(func, partial):
            to_record = func.func
        else:
            # get the underlying method for bound methods:
            to_record = getattr(func, '__func__', func)
        seen.add(to_record)
        return original(executor, func, *args)

    loop.run_in_executor = recording_run_in_executor
    try:
        yield
    finally:
        loop.run_in_executor = original

    not_seen = set(expected) - seen
    assert not not_seen, f'{not_seen} not run in a thread, seen: {seen}'


class TestContext:

    @pytest.mark.asyncio
    async def test_call_is_async(self):
        context = Context(paradigm=paradigms.asyncio)

        def it():
            return 'bar'

        result = context.call(it)
        assert asyncio.iscoroutine(result)
        with must_run_in_thread(it):
            compare(await result, expected='bar')

    @pytest.mark.asyncio
    async def test_call_async(self):
        context = Context()

        async def it():
            return 'bar'

        with no_threads():
            compare(await context.call(it), expected='bar')
