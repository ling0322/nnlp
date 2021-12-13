import io
import unittest

from nnlp.fst import FstArc, Fst

class TestFst(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_read(self):
        r''' test the tokenizer for a simple rule '''

        ilabel_data = '''<eps> 0\nA 1\nB 2\n'''
        olabel_data = '''<eps> 0\nC 1\nD 2\n'''
        fst_data = '0 1 0 0 1.0\n' + \
                   '1 1 1 2 0.5\n' + \
                   '1 2 2 1 0.5\n' + \
                   '2 0 2 2 1.0\n' + \
                   '0 0.0\n'

        fst = Fst.from_text(io.StringIO(ilabel_data), io.StringIO(olabel_data),
                            io.StringIO(fst_data))

        self.assertListEqual(fst._arcs, [
            FstArc(0, 1, "", "", 1.0),
            FstArc(1, 1, "A", "D", 0.5),
            FstArc(1, 2, "B", "C", 0.5),
            FstArc(2, 0, "B", "D", 1.0)
        ])

        self.assertDictEqual(
            fst._graph, {
                0: {
                    '': [FstArc(0, 1, "", "", 1.0)]
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
