import io
import unittest

from nnlp.decoder import FstDecoder
from nnlp.fst import Fst

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.rule_parser import RuleParser
from nnlp_tools.grammar import Grammar
from nnlp_tools.grammar_fst_builder import GrammarFstBuilder
from nnlp_tools.util import SourcePosition
from nnlp_tools.lexicon_fst_builder import LexiconFstBuilder
from nnlp_tools.mutable_fst import MutableFst

class TestFstDecoder(unittest.TestCase):

    def test_decoder(self):
        ''' test the decoder '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()
        fst_builder = GrammarFstBuilder()

        rules = parser(*tokenizer('<root> ::= ("hi":_ _:"hello")* '), SourcePosition())
        grammar = Grammar(rules, "root")

        mutable_fst = MutableFst()
        fst_builder(grammar, mutable_fst)

        json_io = io.StringIO(mutable_fst.to_json())
        fst = Fst.from_json(json_io)

        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence('hihihi'), ["hello"] * 3)

    def test_decoder_escape_symbol(self):
        ''' test the decoder with FST build with unknown_symbol="output"  '''

        fst_builder = LexiconFstBuilder()
        lexicon = [('\#0', ('\<eps\>', '\#1'), 0)]

        mutable_fst = MutableFst()
        fst_builder(lexicon, mutable_fst)

        json_io = io.StringIO(mutable_fst.to_json())
        fst = Fst.from_json(json_io)
        decoder = FstDecoder(fst)
        self.assertListEqual(decoder.decode_sequence(['<eps>', '#1']), ['#0'])

    def test_decoder_unk_output(self):
        ''' test the decoder with FST build with unknown_symbol="output"  '''

        fst_builder = LexiconFstBuilder()
        lexicon = [('hi', ('h', 'i'), 0)]

        mutable_fst = MutableFst()
        fst_builder(lexicon, mutable_fst)
        mutable_fst.add_arc(0, 0, '<unk>', '<capture>')

        json_io = io.StringIO(mutable_fst.to_json())
        fst = Fst.from_json(json_io)
        decoder = FstDecoder(fst)

        self.assertListEqual(decoder.decode_sequence('hibar'), ['hi', 'b', 'a', 'r'])
        
    def test_decoder_unk_ignore(self):
        ''' test the decoder with FST build with unknown_symbol="ignore"  '''

        fst_builder = LexiconFstBuilder()
        lexicon = [('hi', ('h', 'i'), 0)]

        mutable_fst = MutableFst()
        fst_builder(lexicon, mutable_fst)
        mutable_fst.add_arc(0, 0, '<unk>', '<capture_eps>')

        json_io = io.StringIO(mutable_fst.to_json())
        fst = Fst.from_json(json_io)
        decoder = FstDecoder(fst)

        outputs = decoder.decode_sequence('hibar')
        self.assertListEqual(outputs, ['hi'])
