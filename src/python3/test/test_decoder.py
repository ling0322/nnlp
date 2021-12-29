import io
import unittest

from nnlp.decoder import FstDecoder
from nnlp.fst import Fst

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.rule_parser import RuleParser
from nnlp_tools.fst_generator import FSTGenerator
from nnlp_tools.util import SourcePosition, generate_rule_set
from nnlp_tools.lexicon_fst_generator import LexiconFSTGenerator
from nnlp_tools.fst_writer import TextFSTWriter

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

    def test_decoder_escape_symbol(self):
        ''' test the decoder with FST build with unknown_symbol="output"  '''

        fst_generator = LexiconFSTGenerator()
        lexicon = [('\#0', ('\<eps\>', '\#1'), 0)]

        f_fst = io.StringIO()
        f_isym = io.StringIO()
        f_osym = io.StringIO()

        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer)

        fst = Fst.from_text(io.StringIO(f_isym.getvalue()), io.StringIO(f_osym.getvalue()),
                            io.StringIO(f_fst.getvalue()))
        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence(['<eps>', '#1']), ['#0'])

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
        outputs = decoder.decode_sequence('hibar')
        self.assertListEqual(outputs, ['hi'])
