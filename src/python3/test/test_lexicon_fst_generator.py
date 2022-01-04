''' unit test for LexiconFstBuilder '''
import unittest
import math
import io

from nnlp_tools.lexicon_fst_builder import LexiconFstBuilder
from nnlp_tools.fst_writer import FstWriter

from .util import trim_text


class TestLexiconFstBuilder(unittest.TestCase):
    ''' unit test class for LexiconFstBuilder '''

    def test_fst_generator(self):
        r''' test the LexiconFstBuilder '''

        fst_builder = LexiconFstBuilder()

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        with FstWriter(f_fst, f_isym, f_osym) as fst_writer:
            fst_builder([('hi', ('h', 'i'), -0.69), ('hello', ('h', 'e', 'l', 'l', 'o'), -0.36)],
                        fst_writer)

        self.assertEqual(
            f_fst.getvalue(),
            trim_text("""0 1 1 1 -0.69
                1 0 2 0 0
                0 2 1 2 -0.36
                2 3 3 0 0
                3 4 4 0 0
                4 5 4 0 0
                5 0 5 0 0
                0 0.0
                """))

    def test_add_disambig(self):
        r''' test the LexiconFstBuilder '''

        fst_builder = LexiconFstBuilder()
        lexicon = [('fo', ('f', 'o'), -0.69), ('foo', ('f', 'o', 'o'), -0.36),
                   ('bar', ('f', 'o', 'o'), -0.36)]

        self.assertListEqual(fst_builder._add_disambig(lexicon), [
            ('fo', ('f', 'o', '#1'), -0.69),
            ('foo', ('f', 'o', 'o', '#1'), -0.36),
            ('bar', ('f', 'o', 'o', '#2'), -0.36),
        ])

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        with FstWriter(f_fst, f_isym, f_osym) as fst_writer:
            fst_builder(lexicon, fst_writer)
        self.assertEqual(
            f_fst.getvalue(),
            trim_text("""0 1 1 1 -0.69
                1 2 2 0 0
                2 0 3 0 0
                0 3 1 2 -0.36
                3 4 2 0 0
                4 5 2 0 0
                5 0 3 0 0
                0 6 1 3 -0.36
                6 7 2 0 0
                7 8 2 0 0
                8 0 4 0 0
                0 0.0
                """))
