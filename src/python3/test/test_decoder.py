import io
import unittest

from nnlp.decoder import FstDecoder
from nnlp.bnf_tokenizer import BNFTokenizer
from nnlp.rule_parser import RuleParser
from nnlp.fst_generator import FSTGenerator
from nnlp.util import SourcePosition, generate_rule_set
from nnlp.fst import TextFSTWriter, Fst
from nnlp.lexicon_fst_generator import LexiconFSTGenerator


class TestFstDecoder(unittest.TestCase):

    def test_decoder(self):
        ''' test the decoder '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()
        fst_generator = FSTGenerator()

        rules = parser(*tokenizer('<root> ::= ("hi":_ _:"hello")* '), SourcePosition())

        rule_set = generate_rule_set(rules)
        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(rule_set, 'root', fst_writer)
        fst = Fst.from_text(io.StringIO(f_isym.getvalue()), io.StringIO(f_osym.getvalue()),
                            io.StringIO(f_fst.getvalue()))

        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence('hihihi'), ["hello"] * 3)

    def test_decoder_unk_output(self):
        ''' test the decoder with FST build with unknown_symbol="output"  '''

        fst_generator = LexiconFSTGenerator()
        lexicon = [('hi', ('h', 'i'), 0)]

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer, unknown_symbol='output')

        fst = Fst.from_text(io.StringIO(f_isym.getvalue()), io.StringIO(f_osym.getvalue()),
                            io.StringIO(f_fst.getvalue()))
        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence('hibar'), ['hi', 'b', 'a', 'r'])
        
    def test_decoder_unk_ignore(self):
        ''' test the decoder with FST build with unknown_symbol="ignore"  '''

        fst_generator = LexiconFSTGenerator()
        lexicon = [('hi', ('h', 'i'), 0)]

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer, unknown_symbol='ignore')

        fst = Fst.from_text(io.StringIO(f_isym.getvalue()), io.StringIO(f_osym.getvalue()),
                            io.StringIO(f_fst.getvalue()))
        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence('hibar'), ['hi'])
