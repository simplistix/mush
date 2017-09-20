# compatibility module for different python versions
import sys
from collections import OrderedDict
from .markers import Marker


if sys.version_info[:2] < (3, 0):
    PY2 = True
    from functools import partial
    from inspect import getargspec, ismethod, isclass, isfunction

    class Parameter(object):
        POSITIONAL_ONLY = Marker('POSITIONAL_ONLY')
        POSITIONAL_OR_KEYWORD = kind = Marker('POSITIONAL_OR_KEYWORD')
        KEYWORD_ONLY = Marker('KEYWORD_ONLY')
        empty = default = Marker('empty')

    class Signature(object):
        __slots__ = 'parameters'

    def signature(obj):
        sig = Signature()
        sig.parameters = params = OrderedDict()

        bound_args = 0
        extra_kw = {}
        if isclass(obj):
            obj = obj.__init__
        elif isinstance(obj, partial):
            bound_args = len(obj.args)
            extra_kw = obj.keywords
            obj = obj.func
        if not (isfunction(obj) or ismethod(obj)):
            obj = obj.__call__
        if not (isfunction(obj) or ismethod(obj)):
            return sig
        spec = getargspec(obj)
        spec_args = spec.args
        if callable(obj) and not isfunction(obj):
            bound_args += 1
        if bound_args:
            spec_args = spec.args[bound_args:]

        defaults_count = 0 if spec.defaults is None else len(spec.defaults)
        default_start = len(spec_args) - defaults_count
        for i, arg in enumerate(spec_args):
            params[arg] = p = Parameter()
            p.name = arg
            if i >= default_start:
                p.default = True

        for name in extra_kw:
            p = params[name]
            p.default = True
            p.kind = p.KEYWORD_ONLY

        seen_keyword_only = False
        for p in params.values():
            if p.kind is p.KEYWORD_ONLY:
                seen_keyword_only = True
            elif seen_keyword_only:
                p.kind = p.KEYWORD_ONLY

        return sig

else:
    PY2 = False
    from inspect import signature

NoneType = type(None)
