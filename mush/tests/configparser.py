import sys

if sys.version_info[:2] > (3, 0):
    from configparser import RawConfigParser
else:
    from ConfigParser import RawConfigParser

    
