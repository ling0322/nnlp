import io
import tempfile
import unittest

from os import path

from nnlp.symbol import EPS_SYM, make_disambig_symbol
from nnlp_tools.fst_writer import FstWriter

from .util import trim_text

class TestFst(unittest.TestCase):
    ''' unit test class for FstWriter '''

    def test_fst_writer(self):
        ''' test the FstWriter '''

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        with FstWriter(f_fst, f_isym, f_osym) as fst_writer:
            state_1 = fst_writer.create_state()
            state_2 = fst_writer.create_state()
            fst_writer.add_arc(0, state_1, '\#unk', '\#0')
            fst_writer.add_arc(state_1, state_2, make_disambig_symbol(1), EPS_SYM)
            fst_writer.set_final_state(state_2)

        self.assertEqual(f_fst.getvalue(), "0 1 1 1 0.0\n1 2 2 0 0.0\n2 0.0\n")
        self.assertEqual(f_isym.getvalue(), trim_text("<eps> 0\n\#unk 1\n#1 2\n"))
        self.assertEqual(f_osym.getvalue(), trim_text("<eps> 0\n\#0 1\n"))

    def test_fst_writer_readonly_symbol_table(self):
        ''' test the FstWriter with readonly i/o-symbols '''

        with tempfile.TemporaryDirectory() as tmpdir:
            isyms_file = path.join(tmpdir, "isyms.txt")
            with open(isyms_file, 'w') as f:
                f.write('<eps> 0\nh 1\ni 2\n')
            osyms_file = path.join(tmpdir, "osyms.txt")
            with open(osyms_file, 'w') as f:
                f.write('<eps> 0\nhi 1\n')
            
            f_fst = io.StringIO()
            with FstWriter(f_fst, isyms_file, osyms_file) as fst_writer:
                state_1 = fst_writer.create_state()
                state_2 = fst_writer.create_state()
                fst_writer.add_arc(0, state_1, 'h', 'hi')
                fst_writer.add_arc(state_1, state_2, 'i', '<eps>')
                fst_writer.set_final_state(state_2)

            self.assertEqual(f_fst.getvalue(), "0 1 1 1 0.0\n1 2 2 0 0.0\n2 0.0\n")

            # unknown symbol
            f_fst = io.StringIO()
            with FstWriter(f_fst, isyms_file, osyms_file) as fst_writer:
                state_1 = fst_writer.create_state()
                self.assertRaises(Exception, fst_writer.add_arc, 0, state_1, 'hi', 'hi')
