import io
import unittest
import tempfile

from os import path
from nnlp.fst import Fst
from nnlp.symbol import EPS_SYM, make_disambig_symbol
from nnlp_tools.mutable_fst import MutableFst

from .util import trim_text


class TestFst(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_from_json(self):
        ''' test Fst.from_json '''
        with tempfile.TemporaryDirectory() as tmpdir:
            mutable_fst = MutableFst()
            state_1 = mutable_fst.create_state()
            state_2 = mutable_fst.create_state()
            mutable_fst.add_arc(0, state_1, EPS_SYM, EPS_SYM, 1)
            mutable_fst.add_arc(state_1, state_1, 'A', 'D', 0.5)
            mutable_fst.add_arc(state_1, state_2, 'B', 'C', 0.5)
            mutable_fst.add_arc(state_2, 0, 'B', 'D', 1)
            mutable_fst.set_final_state(0)

            filename = path.join(tmpdir, 'fst.json')
            with open(filename, 'w') as f:
                f.write(mutable_fst.to_json())

            fst = Fst.from_json(filename)
            self.assertListEqual(fst._graph, [{
                '<eps>': [[1, '<eps>', 1.0]]
            }, {
                'A': [[1, 'D', 0.5]],
                'B': [[2, 'C', 0.5]]
            }, {
                'B': [[0, 'D', 1.0]]
            }])
            self.assertDictEqual(fst._final_weights, {0: 0.0})
            self.assertDictEqual(fst._isymbol_dict, {
                EPS_SYM: 0,
                'A': 1,
                'B': 2
            })
