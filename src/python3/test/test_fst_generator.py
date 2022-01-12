import io
import unittest

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.grammar import Grammar
from nnlp_tools.rule_parser import RuleParser
from nnlp_tools.grammar_fst_builder import GrammarFstBuilder
from nnlp_tools.util import SourcePosition
from nnlp_tools.fst_writer import FstWriter

from .util import trim_text


class TestFSTGenerator(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_generator(self):
        r''' test the tokenizer for a simple rule '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()
        fst_builder = GrammarFstBuilder()

        rules = parser(*tokenizer('<root> ::= ("hi")* '), SourcePosition())
        grammar = Grammar(rules, "root")

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        with FstWriter(f_fst, f_isym, f_osym) as fst_writer:
            fst_builder(grammar, fst_writer)

        self.assertEqual(
            f_fst.getvalue(),
            trim_text("""0 2 0 0 0.0
                2 3 1 1 0.0
                3 4 2 2 0.0
                4 2 0 0 0.0
                2 1 0 0 0.0
                1 0.0
                """))
