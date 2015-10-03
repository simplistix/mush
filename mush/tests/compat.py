# compatibility module for different python versions
from nose import SkipTest
import os
import sys

if sys.version_info[:2] > (3, 2):
    PY32 = True
else:
    PY32 = False

if sys.version_info[:2] > (3, 0):
    PY3 = True
else:
    PY3 = False

