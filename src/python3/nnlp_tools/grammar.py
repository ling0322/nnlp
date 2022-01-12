'''  Grammer stores all rules in definition file '''

from __future__ import annotations

import math

from .rule import Rule

class Grammar:
    '''
    stores a collection of rules for a grammar. it will call RuleParser to normalize rules provided
    by parameter
    Args:
        rules (list[Rule]): rules in the grammar
        root_class (str): root class in the grammar '''
    
    def __init__(self, rules: list[Rule], root_class: str) -> None:
        self._rule_set = self._generate_rule_set(rules)
        self._root_class = root_class

        # normalize weight
        self._normalize_weight()


    @property
    def rule_set(self) -> dict[str, set[Rule]]:
        return self._rule_set

    @property
    def root_class(self) -> str:
        return self._root_class

    def _normalize_weight(self) -> None:
        ''' for each class normalize sum of its rule weights to 1, then apply -math.log '''

        for rules in self._rule_set.values():
            weight_sum = sum(map(lambda r: r.weight, rules))
            for rule in rules:
                rule.weight = -math.log(rule.weight / weight_sum)

    def _generate_rule_set(self, rules: list[Rule]) -> dict[str, set[Rule]]:
        ''' generate rule set from rule list '''

        rule_set: dict[str, set[Rule]] = {}
        for rule in rules:
            if rule.class_name not in rule_set:
                rule_set[rule.class_name] = set()
            rule_set[rule.class_name].add(rule)
        
        return rule_set
