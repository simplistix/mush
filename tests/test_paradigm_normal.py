from unittest.mock import Mock

from testfixtures import compare

from mush.paradigms import Call
from mush.paradigms.normal_ import Normal


class TestParadigm:

    def test_claim(self):
        # Since this is the "backstop" paradigm, it always claims things
        p = Normal()
        assert p.claim(lambda x: None)

    def test_process_single(self):
        obj = Mock()

        def calls():
            yield Call(obj, ('a',), {'b': 'c'})

        p = Normal()

        compare(p.process(calls()), expected=obj.return_value)

        obj.assert_called_with('a', b='c')

    def test_process_multiple(self):
        mocks = Mock()

        results = []

        def calls():
            results.append((yield Call(mocks.obj1, ('a',), {})))
            results.append((yield Call(mocks.obj2, ('b',), {})))
            yield Call(mocks.obj3, ('c',), {})

        p = Normal()

        compare(p.process(calls()), expected=mocks.obj3.return_value)

        compare(results, expected=[
            mocks.obj1.return_value,
            mocks.obj2.return_value,
        ])
