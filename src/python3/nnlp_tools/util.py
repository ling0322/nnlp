

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from nnlp.symbol import EPS_SYM, UNK_SYM, Disambig, Epsilon, Unknown

if TYPE_CHECKING:
    from nnlp.symbol import Symbol

    from .lexicon_fst_generator import Lexicon
    from .rule import Rule

class BNFSyntaxError(Exception):
    r''' raised when an invaid BNF expression string occured '''
    pass


def read_lexicon(filename: str) -> Lexicon:
    ''' read lexicon from file, the lexicon format is:
        <word> <probability> <symbol1> <symbol2> ... <symbolN>\\n '''
    lexicon: Lexicon = []
    with open(filename, encoding='utf-8') as f:
        for line in f:
            try:
                row = line.strip().split()
                assert len(row) >= 3
                word = row[0]
                weight = -math.log(float(row[1]))
                symbols = row[2:]
                lexicon.append((word, symbols, weight))
            except Exception as _:
                raise Exception(f'unexpected line in {filename}: {line.strip()}')

    return lexicon

class SourcePosition:
    r''' represent a position in source file, usually it is (filename, line number)  '''
    def __init__(self, fileanme: str = None, line: int = None):
        self._filename = fileanme
        self._line = line

def generate_rule_set(rule_list: list[Rule]) -> dict[str, set[Rule]]:
    r''' generate rule set from rule list '''

    rule_set: dict[str, set[Rule]] = {}
    for rule in rule_list:
        if rule.class_name not in rule_set:
            rule_set[rule.class_name] = set()
        rule_set[rule.class_name].add(rule)
    
    return rule_set

