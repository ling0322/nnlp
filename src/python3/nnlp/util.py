

from __future__ import annotations

from typing import Dict, List, Optional, Set, TYPE_CHECKING
if TYPE_CHECKING:
    from .rule import Rule

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
