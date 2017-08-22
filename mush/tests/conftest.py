from mush import returns, requires
from .compat import PY2
from mock import Mock
from testfixtures.comparison import register
import pytest


def pytest_ignore_collect(path):
    if 'py3' in path.basename and PY2:
        return True


@pytest.fixture()
def mock():
    return Mock()


def compare_requires(x, y, context):
    if sorted(x) == sorted(y):
        return
    return (context.label('x', repr(x)) +
            ' != ' +
            context.label('y', repr(y))) # pragma: no cover


def compare_returns(x, y, context):
    if x.args == y.args:
        return
    return (context.label('x', repr(x)) +
            ' != ' +
            context.label('y', repr(y))) # pragma: no cover


register(requires, compare_requires)
register(returns, compare_returns)
