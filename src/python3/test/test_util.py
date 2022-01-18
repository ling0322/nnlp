import unittest
import math

from nnlp_tools.util import lexicon_add_ilabel_selfloop


class TestToolsUtil(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_lexicon_add_ilabel_selfloop(self):
        ''' test lexicon_add_ilabel_selfloop() '''
        lexicon = [
            ('one', ('o', 'n', 'e'), 0),
            ('two', ('t', 'w', 'o'), 0),
            ('three', ('t', 'h', 'r', 'e', 'e'), 0),
            ('n', ('n'), 0),
            ('e', ('e'), 0),
            ('w', ('w'), 0),
        ]
        asl_lexicon = lexicon_add_ilabel_selfloop(lexicon)
        self.assertListEqual(asl_lexicon, lexicon + [
            ('h', ('h',), -math.log(0.1)),
            ('o', ('o',), -math.log(0.1)),
            ('r', ('r',), -math.log(0.1)),
            ('t', ('t',), -math.log(0.1)),
        ])
