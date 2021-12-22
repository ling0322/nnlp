

from __future__ import annotations

from typing import Dict, List, Optional, Set, TYPE_CHECKING

from .symbol import EPS_SYM, UNK_SYM, Disambig, Epsilon, Unknown
if TYPE_CHECKING:
    from .rule import Rule
    from .symbol import Symbol

class BNFSyntaxError(Exception):
    r''' raised when an invaid BNF expression string occured '''
    pass


class SourcePosition:
    r''' represent a position in source file, usually it is (filename, line number)  '''
    def __init__(self, fileanme: str = None, line: int = None):
        self._filename = fileanme
        self._line = line

def generate_rule_set(rule_list: List[Rule]) -> Dict[str, Set[Rule]]:
    r''' generate rule set from rule list '''

    rule_set: Dict[str, Set[Rule]] = {}
    for rule in rule_list:
        if rule.class_name not in rule_set:
            rule_set[rule.class_name] = set()
        rule_set[rule.class_name].add(rule)
    
    return rule_set

def encode_symbol(symbol: Symbol) -> str:
    ''' encode the symbol to string '''
    
    if isinstance(symbol, Disambig):
        return str(symbol)
    elif isinstance(symbol, Unknown):
        return str(UNK_SYM)
    elif isinstance(symbol, Epsilon):
        return str(EPS_SYM)
    elif isinstance(symbol, str):
        symbol = symbol.replace('\\', '\\\\')
        symbol = symbol.replace('#', '\\#')
        return symbol
    else:
        raise Exception('unexpected symbol type')
