import sys

PY_VERSION = sys.version_info[:2]

PY_37_PLUS = PY_VERSION >= (3, 7)

try:
    from typing import _GenericAlias
except ImportError:
    class _GenericAlias:
        pass
