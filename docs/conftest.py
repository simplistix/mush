from doctest import REPORT_NDIFF, ELLIPSIS

from sybil import Sybil
from sybil.parsers.capture import parse_captures
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser

sybil_collector = Sybil(
    parsers=[
        DocTestParser(optionflags=REPORT_NDIFF|ELLIPSIS),
        CodeBlockParser(),
        parse_captures,
    ],
    pattern='*.txt',
).pytest()


# def pytest_collect_file(parent, path):
#     return sybil_collector(parent, path)
