''' unit test for LexiconFSTGenerator '''
import unittest
import math
import io

from nnlp.lexicon_fst_generator import LexiconFSTGenerator
from nnlp.fst import TextFstWriter


class TestLexiconFSTGenerator(unittest.TestCase):
    r''' unit test class for LexiconFSTGenerator '''

    def _trim_text(self, text: str) -> str:
        r''' removing leading space in text'''

        return '\n'.join(map(lambda t: t.strip(), text.split('\n')))

    def test_fst_generator(self):
        r''' test the LexiconFSTGenerator '''

        fst_generator = LexiconFSTGenerator()
        
        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFstWriter(f_fst, f_isym, f_osym)
        fst_generator([('hi', -0.69), ('hello', -0.36)], fst_writer)
        
        self.assertEqual(
            f_fst.getvalue(),
            self._trim_text("""0 1 1 1 -0.69
            1 0 2 0 -0.69
            0 2 1 2 -0.36
            2 3 3 0 -0.36
            3 4 4 0 -0.36
            4 5 4 0 -0.36
            5 0 5 0 -0.36
            0 0.0
            """))
