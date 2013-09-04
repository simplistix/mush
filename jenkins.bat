%PYTHON_EXE% bootstrap.py
CHOICE /T 20 /C w /D w
bin\buildout
bin\nosetests --nologcapture --with-xunit --with-cov --cov=mush
bin\docpy setup.py sdist
