import io
import unittest

from nnlp.fst import EPS_SYM, Disambig, FstArc, Fst, TextFSTWriter
from nnlp.symbol import EPS_SYM_ID

from .util import trim_text


class TestFst(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_read(self):
        r''' test the tokenizer for a simple rule '''

        ilabel_data = '''#eps 0\n#unk 1\nA 2\nB 3\n'''
        olabel_data = '''#unk 0\n#unk 1\nC 2\nD 3\n'''
        fst_data = '0 1 0 0 1.0\n' + \
                   '1 1 2 3 0.5\n' + \
                   '1 2 3 2 0.5\n' + \
                   '2 0 3 3 1.0\n' + \
                   '0 0.0\n'

        fst = Fst.from_text(io.StringIO(ilabel_data), io.StringIO(olabel_data),
                            io.StringIO(fst_data))

        self.assertListEqual(fst._arcs, [
            FstArc(0, 1, EPS_SYM, EPS_SYM, 1.0),
            FstArc(1, 1, "A", "D", 0.5),
            FstArc(1, 2, "B", "C", 0.5),
            FstArc(2, 0, "B", "D", 1.0)
        ])

        self.assertDictEqual(
            fst._graph, {
                0: {
                    '#eps': [FstArc(0, 1, EPS_SYM, EPS_SYM, 1.0)]
                },
                1: {
                    'A': [FstArc(1, 1, "A", "D", 0.5)],
                    'B': [FstArc(1, 2, "B", "C", 0.5)]
                },
                2: {
                    'B': [FstArc(2, 0, "B", "D", 1.0)]
                }
            })

        self.assertDictEqual(fst._final_states, {0: 0.0})

    def test_text_fst_writer(self):
        ''' test the TextFSTWriter '''

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        state_1 = fst_writer.create_state()
        state_2 = fst_writer.create_state()
        fst_writer.add_arc(0, state_1, '#unk', '#0')
        fst_writer.add_arc(state_1, state_2, Disambig(0), EPS_SYM)
        fst_writer.set_final_state(state_2)
        fst_writer.write()

        self.assertEqual(f_fst.getvalue(), "0 1 2 2 0.0\n1 2 10000000 0 0.0\n2 0.0\n")
        self.assertEqual(f_isym.getvalue(), trim_text("#eps 0\n#_unk 1\n#unk 2\n#_0 10000000\n"))

    def test_disambig(self):
        ''' test class Disambig '''

        disambig_1 = Disambig(1)
        disambig_1a = Disambig(1)
        disambig_2 = Disambig(2)

        self.assertIs(disambig_1, disambig_1a)
        self.assertIsNot(disambig_1, disambig_2)
