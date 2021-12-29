''' unit test for LexiconFSTGenerator '''
import unittest
import math
import io

from nnlp_tools.lexicon_fst_generator import LexiconFSTGenerator
from nnlp_tools.fst_writer import TextFSTWriter

from .util import trim_text


class TestLexiconFSTGenerator(unittest.TestCase):
    ''' unit test class for LexiconFSTGenerator '''

    def test_fst_generator(self):
        r''' test the LexiconFSTGenerator '''

        fst_generator = LexiconFSTGenerator()

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator([('hi', ('h', 'i'), -0.69), ('hello', ('h', 'e', 'l', 'l', 'o'), -0.36)],
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
        r''' test the LexiconFSTGenerator '''

        fst_generator = LexiconFSTGenerator()
        lexicon = [('fo', ('f', 'o'), -0.69), ('foo', ('f', 'o', 'o'), -0.36),
                   ('bar', ('f', 'o', 'o'), -0.36)]

        self.assertListEqual(fst_generator._add_disambig(lexicon), [
            ('fo', ('f', 'o', '#1'), -0.69),
            ('foo', ('f', 'o', 'o', '#1'), -0.36),
            ('bar', ('f', 'o', 'o', '#2'), -0.36),
        ])

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer)
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

    def test_unknown_output(self):
        r''' test the LexiconFSTGenerator '''

        fst_generator = LexiconFSTGenerator()
        lexicon = [('hi', ('h', 'i'), 0)]

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer, unknown_symbol='output')

        self.assertEqual(
            f_fst.getvalue(),
            trim_text("""0 1 1 1 0
                1 0 2 0 0
                0 0 3 2 2.303
                0 0.0
                """))

    def test_unknown_ignore(self):
        r''' test the LexiconFSTGenerator '''

        fst_generator = LexiconFSTGenerator()
        lexicon = [('hi', ('h', 'i'), 0)]

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer, unknown_symbol='ignore')

        self.assertEqual(
            f_fst.getvalue(),
            trim_text("""0 1 1 1 0
                1 0 2 0 0
                0 0 3 2 2.303
                0 0.0
                """))
        self.assertEqual(f_isym.getvalue(), trim_text("""<eps> 0\nh 1\ni 2\n<unk> 3\n"""))
        self.assertEqual(f_osym.getvalue(), trim_text("""<eps> 0\nhi 1\n<capture_eps> 2\n"""))
