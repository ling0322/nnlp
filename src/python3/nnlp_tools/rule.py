from __future__ import annotations

from typing import Optional

from .util import SourcePosition
from .common import BNFToken


class Rule:
    r''' represents a BNF rule in grammar
    Args:
        class_name (str): name of the class (left side of ::=)
        tokens (List[BNFToken]): tokens in the rule (right side of ::=)
        position (SourcePosition): position in source file
        flag (str): flag of rule, possible values: '*', '?' '''

    def __init__(
        self,
        class_name: str,
        tokens: list[BNFToken],
        position: Optional[SourcePosition] = None,
        flag: str = '',
        weight: float = 1.0,
    ):
        self.class_name = class_name
        self.tokens = tokens
        self.position = position
        self.flag = flag
        self.weight = weight

    def __repr__(self):
        t = f'Rule(<{self.class_name}> ::= {" ".join(map(str, self.tokens))}'
        if self.flag:
            t += f'; F="{self.flag}" W={self.weight}'
        t += ')'
        return t

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Rule):
            return False
        return self.class_name == o.class_name and self.tokens == o.tokens and self.flag == o.flag and self.weight == o.weight
