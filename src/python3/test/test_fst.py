import io
import unittest

from nnlp.fst import Fst
from nnlp.symbol import EPS_SYM, make_disambig_symbol
from nnlp_tools.fst_writer import TextFSTWriter

from .util import trim_text


class TestFst(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_read(self):
        r''' test the tokenizer for a simple rule '''

        ilabel_data = '''<eps> 0\n<unk> 1\nA 2\nB 3\n'''
        olabel_data = '''<eps> 0\n<unk> 1\nC 2\nD 3\n'''
        fst_data = '0 1 0 0 1.0\n' + \
                   '1 1 2 3 0.5\n' + \
                   '1 2 3 2 0.5\n' + \
                   '2 0 3 3 1.0\n' + \
                   '0 0.0\n'

        fst = Fst.from_text(io.StringIO(ilabel_data), io.StringIO(olabel_data),
                            io.StringIO(fst_data))

        self.assertListEqual(fst._graph, [{
            '<eps>': [(1, '<eps>', 1.0)]
        }, {
            'A': [(1, 'D', 0.5)],
            'B': [(2, 'C', 0.5)]
        }, {
            'B': [(0, 'D', 1.0)]
        }])

        self.assertDictEqual(fst._final_weights, {0: 0.0})

    def test_fst_json_save_load(self):
        ''' test FST json format save and load '''

        ilabel_data = '''<eps> 0\n<unk> 1\nA 2\nB 3\n'''
        olabel_data = '''<eps> 0\n<unk> 1\nC 2\nD 3\n'''
        fst_data = '0 1 0 0 1.0\n' + \
                   '1 1 2 3 0.5\n' + \
                   '1 2 3 2 0.5\n' + \
                   '2 0 3 3 1.0\n' + \
                   '0 0.0\n'

        fst = Fst.from_text(io.StringIO(ilabel_data), io.StringIO(olabel_data),
                            io.StringIO(fst_data))

        f_json = io.StringIO()
        fst.to_json(f_json)

        fst_json = Fst.from_json(io.StringIO(f_json.getvalue()))

        self.assertListEqual(fst._graph, [{
            '<eps>': [(1, '<eps>', 1.0)]
        }, {
            'A': [(1, 'D', 0.5)],
            'B': [(2, 'C', 0.5)]
        }, {
            'B': [(0, 'D', 1.0)]
        }])
        self.assertDictEqual(fst_json._final_weights, fst._final_weights)
        self.assertDictEqual(fst_json._isymbol_dict, fst._isymbol_dict)

    def test_text_fst_writer(self):
        ''' test the TextFSTWriter '''

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        state_1 = fst_writer.create_state()
        state_2 = fst_writer.create_state()
        fst_writer.add_arc(0, state_1, '\#unk', '\#0')
        fst_writer.add_arc(state_1, state_2, make_disambig_symbol(1), EPS_SYM)
        fst_writer.set_final_state(state_2)
        fst_writer.write()

        self.assertEqual(f_fst.getvalue(), "0 1 1 1 0.0\n1 2 2 0 0.0\n2 0.0\n")
        self.assertEqual(f_isym.getvalue(), trim_text("<eps> 0\n\#unk 1\n#1 2\n"))
        self.assertEqual(f_osym.getvalue(), trim_text("<eps> 0\n\#0 1\n"))
