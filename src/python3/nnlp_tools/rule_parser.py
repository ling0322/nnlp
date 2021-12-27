from typing import Dict, Iterable, List, Set

import itertools

from .common import BNFToken
from .rule import Rule
from .bnf_tokenizer import BNFTokenizer
from .util import BNFSyntaxError, SourcePosition


class RuleParser:
    r''' :
        <city> ::=  "seattle" | "bellevue" 
    to
        <city> ::= "seattle"
        <city> ::= "bellevue"

        <weather> ::=  "weather" "in" ( "seattle" | "bellevue" )
    to
        <weather> ::= "weather" "in" <weather_0001>
        <weather_0001> ::= "seattle"
        <weather_0001> ::= "bellevue"
    '''

    _ALPHABET = 'abcdefghijkmnpqrstuwxyz0123456789'

    def __init__(self):
        self._global_class_set: Set = set()
        self._subrule_count: Dict[str, int] = {}

    def __call__(self, name: str, tokens: List[BNFToken], source: SourcePosition) -> List[Rule]:
        r''' parse a rule into list of rules
             Args:
                 name (str): class name of the rule
                 tokens (List[BNFToken]): tokens of the rule
                 source (SourcePosition): position of the rule in source file '''

        rules: Iterable[Rule] = [Rule(name, tokens, source)]
        rules = sum(map(self._replace_sub_rule, rules), [])
        rules = sum(map(self._split_alternatives, rules), [])
        rules = list(rules)
        for rule in rules:
            self._verify_rule(rule)

        return rules

    def _generate_sub_name(self, name: str) -> str:
        r''' generate sub class name from class name and make sure the sub class name is unique in 
        _global_class_set, for example, 'weather' -> 'weather:a04e' '''

        for i in itertools.count(self._subrule_count.get(name, 0)):
            sub_name = f'{name}_{i:02}'
            if sub_name not in self._global_class_set:
                self._global_class_set.add(sub_name)
                self._subrule_count[name] = i + 1
                break

        return sub_name

    def _replace_sub_rule(self, rule: Rule) -> List[Rule]:
        r''' do two things: 1) replace sub rules. 2) parse flag. For example:
                <weather> ::= ( <city> ) * "weather"
                -->
                <weather> ::= <weather:00aa> "weather" 
                <weather:00aa> ::= <city>   flag="*" '''

        state = 'OUTSIDE'
        rule_dict: Dict[str, Rule] = {}
        rule_tokens: List[BNFToken] = []
        subrule_tokens: List[BNFToken] = []

        for token in itertools.chain(rule.tokens, [BNFToken(BNFToken.END)]):
            if state == 'OUTSIDE':
                if token.type == BNFToken.LEFT_PARENTHESIS:
                    state = 'INSIDE'
                elif token.type == BNFToken.END:
                    state = 'FINISH'
                else:
                    rule_tokens.append(token)
            elif state == 'INSIDE':
                if token.type == BNFToken.RIGHT_PARENTHESIS:
                    # look for '*' or '?'
                    state = 'SUFFIX'
                elif token.type == BNFToken.LEFT_PARENTHESIS:
                    raise BNFSyntaxError(f'only 1 level parenthesis is supported')
                elif token.type == BNFToken.END:
                    raise BNFSyntaxError(f'parenthesis mismatch')
                else:
                    subrule_tokens.append(token)
            elif state == 'SUFFIX':
                subrule_flag: str = ''
                if token.type == BNFToken.QUESTION:
                    subrule_flag = '?'
                    state = 'OUTSIDE'
                elif token.type == BNFToken.ASTERISK:
                    subrule_flag = '*'
                    state = 'OUTSIDE'
                elif token.type == BNFToken.END:
                    state = 'FINISH'
                else:
                    rule_tokens.append(token)
                    state = 'OUTSIDE'

                subrule = Rule(
                    self._generate_sub_name(rule.class_name),
                    subrule_tokens,
                    rule.position,
                    subrule_flag,
                )
                rule_dict[subrule.class_name] = subrule
                rule_tokens.append(BNFToken(BNFToken.CLASS, subrule.class_name))
                subrule_tokens = []

        assert state == 'FINISH'

        # add the new original rule into rules, if the new original rule is just a class mapping to
        # its subclass (<class1> ::= <class1:0a0a>), replace it with the mapped one directly
        if len(rule_tokens) == 1 and rule_tokens[0].type == BNFToken.CLASS and rule_tokens[
                0].value in rule_dict:
            mapped_rule = rule_dict[rule_tokens[0].value]
            new_rule = Rule(rule.class_name, mapped_rule.tokens, mapped_rule.position,
                            mapped_rule.flag)
            del rule_dict[rule_tokens[0].value]
        else:
            new_rule = Rule(rule.class_name, rule_tokens, rule.position, rule.flag)
        rule_dict[new_rule.class_name] = new_rule

        return list(rule_dict.values())

    def _split_alternatives(self, rule: Rule) -> List[Rule]:
        r''' split alternatives definitions into multiple rules, for example,
                 <weather> ::= <city> "weather" | "weather" "in" <city>
                 ->
                 <weather> ::= <city> "weather"
                 <weather> ::= "weather" "in" <city>
             if a rule have flag '?' remove the flag and add an additional rule to _, for example,
                 <hi> ::= ( "hi" | "hello" ) ?
                 ->
                 <hi> ::= "hi"
                 <hi> ::= "hello"
                 <hi> ::= _
             if a rule have flag '*', add a additional class mapping with the flag, for example
                 <hi> ::= ( "hi" | "hello" ) *
                 ->
                 <hi> ::= ( <hi_0001> ) *
                 <hi_0001> ::= "hi"
                 <hi_0001> ::= "hello" '''

        rules: List[Rule] = []
        tokens: List[BNFToken] = []
        for token in rule.tokens:
            if token.type == BNFToken.OR:
                new_rule = Rule(rule.class_name, tokens, rule.position)
                rules.append(new_rule)
                tokens = []
            else:
                tokens.append(token)
        if tokens:
            rules.append(Rule(rule.class_name, tokens, rule.position))

        if rule.flag == '?':
            rules.append(Rule(rule.class_name, [BNFToken(BNFToken.EPSILON)], rule.position))
        elif rule.flag == '*' and len(rules) == 1:
            rules[0].flag = '*'
        elif rule.flag == '*' and len(rules) > 1:
            new_name = self._generate_sub_name(rule.class_name)
            for r in rules:
                r.class_name = new_name
            rules.append(
                Rule(rule.class_name, [BNFToken(BNFToken.CLASS, new_name)], rule.position, '*'))

        return rules

    def _verify_rule(self, rule: Rule) -> None:
        r''' verify if rule is correct. This is the last step of rule parsing. So there is no
        other tokens rather than class and symbol '''

        if not rule.tokens:
            BNFSyntaxError(f'rule or sub-rule is empty')

        if rule.class_name == '<eps>':
            BNFSyntaxError(f'<eps> is reserved for future use')

        for token in rule.tokens:
            if token.type not in {
                    BNFToken.CLASS, BNFToken.SYMBOL, BNFToken.I_SYMBOL, BNFToken.O_SYMBOL,
                    BNFToken.EPSILON
            }:
                raise BNFSyntaxError(f'unexpected token: {token}')
            if token.type == BNFToken.EPSILON and len(rule.tokens) != 1:
                raise BNFSyntaxError(f'_ should be only token of a rule')


