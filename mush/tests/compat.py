# compatibility module for different python versions
import sys

if sys.version_info[:2] > (3, 2):
    PY32 = True
else:
    PY32 = False

    
