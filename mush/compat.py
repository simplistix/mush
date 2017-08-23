# compatibility module for different python versions
import sys

if sys.version_info[:2] < (3, 0):
    PY2 = True
    from itertools import izip_longest as zip_longest
else:
    PY2 = False
    from itertools import zip_longest

NoneType = type(None)
