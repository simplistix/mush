# Copyright (c) 2013 Simplistix Ltd
# See license.txt for license details.

import os
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
from setuptools import setup, find_packages

base_dir = os.path.dirname(__file__)

# read test requirements from tox.ini
config = RawConfigParser()
config.read(os.path.join(base_dir, 'tox.ini'))
test_requires = []
for item in config.get('testenv', 'deps').split():
    test_requires.append(item)
# Tox doesn't need itself, but we need it for testing.
test_requires.append('tox')

setup(
    name='mush',
    version='1.2',
    author='Chris Withers',
    author_email='chris@simplistix.co.uk',
    license='MIT',
    description="Type-based dependency injection for scripts.",
    long_description=open(os.path.join(base_dir,'docs','description.txt')).read(),
    url='http://pypi.python.org/pypi/mush',
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    ],    
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    extras_require=dict(
        test=test_requires,
        )
    )
