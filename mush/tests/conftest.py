from testfixtures.comparison import register, compare_object

from mush.declarations import Requirement


def compare_requirement(x, y, context):
    # make sure this doesn't get refactored away, since we're using it
    # as a proxy to check .ops:
    assert hasattr(x, 'repr')
    return compare_object(x, y, context, ignore_attributes=['ops'])


register(Requirement, compare_requirement)
