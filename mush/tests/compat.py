# compatibility module for different python versions
from nose import SkipTest
import os
import sys

if sys.version_info[:2] < (3, 0):
    PY2 = True
else:
    PY2 = False

