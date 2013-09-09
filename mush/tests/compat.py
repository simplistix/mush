# compatibility module for different python versions
from nose import SkipTest
import os
import sys

def win_skip():
    if os.name=='nt':
        raise SkipTest('Too onerous to get working on Windows')

if sys.version_info[:2] > (3, 2):
    PY32 = True
else:
    PY32 = False

if sys.version_info[:2] > (3, 0):
    PY3 = True
else:
    PY3 = False

