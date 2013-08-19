# compatibility module for different python versions
import sys

if sys.version_info[:2] > (3, 0):
    PY3 = True
else:
    PY3 = False

    
