import pytest
from mock import Mock
from testfixtures.comparison import register, compare_simple

from mush import returns, requires
from mush.declarations import how
from ..compat import PY2


def pytest_ignore_collect(path):
    if 'py3' in path.basename and PY2:
        return True


@pytest.fixture()
def mock():
    return Mock()


def compare_requires(x, y, context):
    diff_args = context.different(x.args, y.args, '.args')
    diff_kw = context.different(x.kw, y.kw, '.args')
    if diff_args or diff_kw:  # pragma: no cover
        return compare_simple(x, y, context)


def compare_returns(x, y, context):
    diff_args = context.different(x.args, y.args, '.args')
    if diff_args:  # pragma: no cover
        return compare_simple(x, y, context)


def compare_how(x, y, context):
    diff_args = context.different(x.type, y.type, '.type')
    diff_names = context.different(x.type, y.type, '.names')
    if diff_args or diff_names:  # pragma: no cover
        return compare_simple(x, y, context)


register(requires, compare_requires)
register(returns, compare_returns)
register(how, compare_how)
