import io
import unittest

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.rule_parser import RuleParser
from nnlp_tools.fst_generator import FSTGenerator
from nnlp_tools.util import SourcePosition, generate_rule_set
from nnlp_tools.fst_writer import TextFSTWriter

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
                2 3 1 1 0.0
                3 4 2 2 0.0
                4 2 0 0 0.0
                2 1 0 0 0.0
                1 0.0
                """))
