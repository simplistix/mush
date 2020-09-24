import sys
from re import search


def pytest_ignore_collect(path):
    file_min_version_match = search(r'_py(\d)(\d)$', path.purebasename)
    if file_min_version_match:
        file_min_version = tuple(int(d) for d in file_min_version_match.groups())
        return sys.version_info < file_min_version
