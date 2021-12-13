import io
import unittest

from nnlp.decoder import FstDecoder
from nnlp.bnf_tokenizer import BNFTokenizer
from nnlp.rule_parser import RuleParser
from nnlp.fst_generator import FSTGenerator
from nnlp.util import SourcePosition, generate_rule_set
from nnlp.fst import TextFstWriter, Fst

class TestFstDecoder(unittest.TestCase):

    def test_decoder(self):
        tokenizer = BNFTokenizer()
        parser = RuleParser()
        fst_generator = FSTGenerator()

        rules = parser(*tokenizer('<root> ::= ("hi":_ _:"hello")* '), SourcePosition())

        rule_set = generate_rule_set(rules)
        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFstWriter(f_fst, f_isym, f_osym)
        fst_generator(rule_set, 'root', fst_writer)
        fst = Fst.from_text(io.StringIO(f_isym.getvalue()), io.StringIO(f_osym.getvalue()),
                            io.StringIO(f_fst.getvalue()))

        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence('hihihi'), ["hello"] * 3)
