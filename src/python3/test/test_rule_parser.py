import io
import unittest

from nnlp_tools.bnf_tokenizer import BNFTokenizer
from nnlp_tools.rule_parser import RuleParser
from nnlp_tools.util import SourcePosition
from nnlp_tools.common import BNFToken
from nnlp_tools.rule import Rule


class TestRuleParser(unittest.TestCase):
    r''' unit test class for BNT tokenizer '''

    def test_rule_parser(self):
        r''' test the tokenizer for a simple rule '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()

        name, tokens = tokenizer('<hello> ::= "hello" ( "," "world")*')
        rules = parser(name, tokens, SourcePosition())
        self.assertListEqual(rules, [
            Rule('hello_00', [BNFToken(BNFToken.SYMBOL, ','),
                              BNFToken(BNFToken.SYMBOL, 'world')],
                 flag='*'),
            Rule('hello',
                 [BNFToken(BNFToken.SYMBOL, 'hello'),
                  BNFToken(BNFToken.CLASS, 'hello_00')])
        ])

        name, tokens = tokenizer('<hi> ::= ("hello" | "world")*')
        rules = parser(name, tokens, SourcePosition())
        self.assertListEqual(rules, [
            Rule('hi_01', [BNFToken(BNFToken.SYMBOL, 'hello')]),
            Rule('hi_01', [BNFToken(BNFToken.SYMBOL, 'world')]),
            Rule('hi', [BNFToken(BNFToken.CLASS, 'hi_01')], flag='*')
        ])

        name, tokens = tokenizer(
            '<weather> ::= <city> "weather" | ( "what\'s" "the" | "what" "is" "the" )? "weather" ( "in" ) ? <city> '
        )
        rules = parser(name, tokens, SourcePosition())
        self.assertListEqual(rules, [
            Rule('weather_00',
                 [BNFToken(BNFToken.SYMBOL, "what\'s"),
                  BNFToken(BNFToken.SYMBOL, "the")]),
            Rule('weather_00', [
                BNFToken(BNFToken.SYMBOL, "what"),
                BNFToken(BNFToken.SYMBOL, "is"),
                BNFToken(BNFToken.SYMBOL, "the")
            ]),
            Rule('weather_00', [BNFToken(BNFToken.EPSILON)]),
            Rule('weather_01', [BNFToken(BNFToken.SYMBOL, "in")]),
            Rule('weather_01', [BNFToken(BNFToken.EPSILON)]),
            Rule('weather',
                 [BNFToken(BNFToken.CLASS, 'city'),
                  BNFToken(BNFToken.SYMBOL, 'weather')]),
            Rule('weather', [
                BNFToken(BNFToken.CLASS, 'weather_00'),
                BNFToken(BNFToken.SYMBOL, 'weather'),
                BNFToken(BNFToken.CLASS, 'weather_01'),
                BNFToken(BNFToken.CLASS, 'city')
            ])
        ])

    def test_rule(self):
        r''' test __hash__ and __eq__ methods in rule '''

        tokenizer = BNFTokenizer()
        parser = RuleParser()
        rule_0 = parser(*tokenizer('<hello> ::= "hello"  "world"'), source=SourcePosition())[0]
        rule_1 = parser(*tokenizer('<hello> ::=  "hello" "world"'), source=SourcePosition())[0]

        self.assertEqual(rule_0, rule_1)
        self.assertEqual(hash(rule_0), hash(rule_1))

        rule_set = set()
        rule_set.add(rule_0)
        rule_set.add(rule_1)
        self.assertEqual(len(rule_set), 1)

        rule_0 = parser(*tokenizer('<e> ::= _'), source=SourcePosition())[0]
        rule_1 = parser(*tokenizer('<e> ::= _'), source=SourcePosition())[0]
        rule_set = set()
        rule_set.add(rule_0)
        rule_set.add(rule_1)
        self.assertEqual(len(rule_set), 1)