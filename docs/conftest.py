from doctest import REPORT_NDIFF, ELLIPSIS

from sybil import Sybil
from sybil.parsers.capture import parse_captures
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser

from mush.compat import PY2

sybil_collector = Sybil(
    parsers=[
        DocTestParser(optionflags=REPORT_NDIFF|ELLIPSIS),
        CodeBlockParser(),
        parse_captures,
    ],
    pattern='*.txt',
).pytest()


def pytest_collect_file(parent, path):
    if not PY2:
        return sybil_collector(parent, path)
