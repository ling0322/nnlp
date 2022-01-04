import io
import unittest

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.util import BNFSyntaxError
from nnlp_tools.common import BNFToken

class TestBNFTokenizer(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_tokenizer(self):
        r''' test the tokenizer for a simple rule '''

        tokenizer = BNFTokenizer()
        name, tokens = tokenizer('<hello> ::= "hello" "world"')
        self.assertEqual(name, 'hello')
        self.assertListEqual(tokens, [
            BNFToken(BNFToken.SYMBOL, 'hello'),
            BNFToken(BNFToken.SYMBOL, 'world'),
        ])

        name, tokens = tokenizer(' <hello> ::= ( "hello" | < world>) \t ')
        self.assertEqual(name, 'hello')
        self.assertListEqual(tokens, [
            BNFToken(BNFToken.LEFT_PARENTHESIS),
            BNFToken(BNFToken.SYMBOL, 'hello'),
            BNFToken(BNFToken.OR),
            BNFToken(BNFToken.CLASS, 'world'),
            BNFToken(BNFToken.RIGHT_PARENTHESIS),
        ])

        name, tokens = tokenizer('<hello> ::= (_:"hello")? ( "world":_ )*')
        self.assertEqual(name, 'hello')
        self.assertListEqual(tokens, [
            BNFToken(BNFToken.LEFT_PARENTHESIS),
            BNFToken(BNFToken.O_SYMBOL, 'hello'),
            BNFToken(BNFToken.RIGHT_PARENTHESIS),
            BNFToken(BNFToken.QUESTION),
            BNFToken(BNFToken.LEFT_PARENTHESIS),
            BNFToken(BNFToken.I_SYMBOL, 'world'),
            BNFToken(BNFToken.RIGHT_PARENTHESIS),
            BNFToken(BNFToken.ASTERISK),
        ])

        name, tokens = tokenizer('<epsilon> ::= _')
        self.assertEqual(name, 'epsilon')
        self.assertListEqual(tokens, [
            BNFToken(BNFToken.EPSILON),
        ])

        self.assertRaises(BNFSyntaxError, tokenizer, "")
        self.assertRaises(BNFSyntaxError, tokenizer, '<hello> ')
        self.assertRaises(BNFSyntaxError, tokenizer, '<hello> ::= ')
        self.assertRaises(BNFSyntaxError, tokenizer, 'hello ::= "hello"')
        self.assertRaises(BNFSyntaxError, tokenizer, 'hello ::= "" "world"')
        self.assertRaises(BNFSyntaxError, tokenizer, '<hello> ::= "hello" "world')
        self.assertRaises(BNFSyntaxError, tokenizer, '<hello world> ::= "hello" "world')
        self.assertRaises(BNFSyntaxError, tokenizer, '<hello:world> ::= "hello" "world')
        self.assertRaises(BNFSyntaxError, tokenizer, 'hello> ::= "hello"')


    def test_tokenizer_macro(self):
        ''' test tokenizer for macro call '''

        tokenizer = BNFTokenizer()
        name, tokens = tokenizer('<hello> ::= !read_lexicon("lexicon.txt") "world"')

        self.assertEqual(name, 'hello')
        self.assertListEqual(tokens, [
            BNFToken(BNFToken.MACRO_READ_LEXICON, 'lexicon.txt'),
            BNFToken(BNFToken.SYMBOL, 'world'),
        ])