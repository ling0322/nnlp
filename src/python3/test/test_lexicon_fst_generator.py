''' unit test for LexiconFstBuilder '''
import unittest
import math
import io

from nnlp_tools.lexicon_fst_builder import LexiconFstBuilder
from nnlp_tools.mutable_fst import MutableFst

from .util import norm_textfst


class TestLexiconFstBuilder(unittest.TestCase):
    ''' unit test class for LexiconFstBuilder '''

    def test_fst_generator(self):
        r''' test the LexiconFstBuilder '''

        fst_builder = LexiconFstBuilder()

        mutable_fst = MutableFst()
        fst_builder([('hi', ('h', 'i'), -0.69),
                     ('hello', ('h', 'e', 'l', 'l', 'o'), -0.36)], mutable_fst)
        t = '''
            0 1 h hi -0.69
            0 2 h hello -0.36
            0
            1 0 i <eps>
            2 3 e <eps>
            3 4 l <eps>
            4 5 l <eps>
            5 0 o <eps>
            '''

        self.assertEqual(norm_textfst(t), norm_textfst(mutable_fst.to_text()))

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

        mutable_fst = MutableFst()
        fst_builder(lexicon, mutable_fst)
        t = '''
            0 1 f fo -0.69
            0 3 f foo -0.36
            0 6 f bar -0.36
            0
            1 2 o <eps>
            2 0 #1 <eps>
            3 4 o <eps>
            4 5 o <eps>
            5 0 #1 <eps>
            6 7 o <eps>
            7 8 o <eps>
            8 0 #2 <eps>
            '''

        self.assertEqual(norm_textfst(t), norm_textfst(mutable_fst.to_text()))
