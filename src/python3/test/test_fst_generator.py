import io
import unittest

from nnlp.bnf_tokenizer import BNFTokenizer
from nnlp.rule_parser import RuleParser
from nnlp.fst_generator import FSTGenerator
from nnlp.util import SourcePosition, generate_rule_set
from nnlp.fst import TextFSTWriter

from .util import trim_text


class TestFSTGenerator(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_fst_generator(self):
        r''' test the tokenizer for a simple rule '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()
        fst_generator = FSTGenerator()

        rules = parser(*tokenizer('<root> ::= ("hi")* '), SourcePosition())

        rule_set = generate_rule_set(rules)
        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(rule_set, 'root', fst_writer)

        self.assertEqual(
            f_fst.getvalue(),
            trim_text("""0 2 0 0 0.0
                2 3 2 2 0.0
                3 4 3 3 0.0
                4 2 0 0 0.0
                2 1 0 0 0.0
                1 0.0
                """))
