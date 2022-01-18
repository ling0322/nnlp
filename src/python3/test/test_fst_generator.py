import io
import unittest

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.grammar import Grammar
from nnlp_tools.rule_parser import RuleParser
from nnlp_tools.grammar_fst_builder import GrammarFstBuilder
from nnlp_tools.util import SourcePosition
from nnlp_tools.mutable_fst import MutableFst

from .util import norm_textfst


class TestFSTGenerator(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_generator(self):
        r''' test the tokenizer for a simple rule '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()
        fst_builder = GrammarFstBuilder()

        rules = parser(*tokenizer('<root> ::= ("hi")* '), SourcePosition())
        grammar = Grammar(rules, "root")

        mutable_fst = MutableFst()
        fst_builder(grammar, mutable_fst)

        t = '''
            0 2 <eps> <eps>
            1
            2 3 h h
            2 1 <eps> <eps>
            3 4 i i
            4 2 <eps> <eps>
            '''
        self.assertEqual(norm_textfst(t), norm_textfst(mutable_fst.to_text()))

