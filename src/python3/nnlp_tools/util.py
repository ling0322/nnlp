

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from nnlp.symbol import escape_symbol

if TYPE_CHECKING:
    from .lexicon_fst_generator import Lexicon
    from .rule import Rule

class BNFSyntaxError(Exception):
    ''' raised when an invaid BNF expression string occured '''
    pass


def read_lexicon(filename: str) -> Lexicon:
    ''' 
    read lexicon from file, the lexicon format is:
        <word> <probability> <symbol1> <symbol2> ... <symbolN>\\n 
    it will also escape symbols and words using escape_symbol() '''
    lexicon: Lexicon = []
    with open(filename, encoding='utf-8') as f:
        for line in f:
            try:
                row = line.strip().split()
                assert len(row) >= 3
                word = escape_symbol(row[0])
                weight = -math.log(float(row[1]))
                symbols = list(map(escape_symbol, row[2:]))
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

