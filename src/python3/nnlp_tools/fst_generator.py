from __future__ import annotations

from .common import BNFToken
from .rule import Rule
from .util import BNFSyntaxError

from nnlp.symbol import EPS_SYM

from nnlp_tools.fst_writer import FstWriter


class FSTGenerator:
    r''' generate FST from rule set '''

    def __call__(self, rule_set: dict[str, set[Rule]], root: str, fst_writer: FstWriter) -> None:
        r''' generate FST from a rule set, and write the FST to file using fst_writer
             Args:
                 rule_set (Dict[str, Set[Rule]]): the rule set
                 root (str): name of the root node
                 fst_writer (FstWriter): the fst writer'''

        self._rule_set: dict[str, set[Rule]] = rule_set
        self._fst_writer: FstWriter = fst_writer

        # build the FST
        begin_state = 0
        final_state = self._generate_class(root, [], begin_state)
        fst_writer.set_final_state(final_state)
        fst_writer.write()

    def _get_symbols(self, token: BNFToken, symbol_type: str) -> list[str]:
        r''' get symbols from a token, return list[str]. symbol_type == 'i' for input
        symbol and 'o' for output symbol '''

        symbols: list[str] = []
        if token.type == BNFToken.SYMBOL or token.type == BNFToken.I_SYMBOL:
            # character mode
            assert not (symbol_type == 'o' and token.type == BNFToken.I_SYMBOL)
            assert token.value
            for ch in token.value:
                symbols.append(ch)
        elif token.type == BNFToken.O_SYMBOL:
            # word mode
            assert symbol_type == 'o'
            assert token.value
            symbols.append(token.value)
        else:
            assert False

        return symbols

    def _generate_class(self, name: str, class_history: list[str], src_state: int) -> int:
        r''' generate FST for one class, returns the last state '''

        # check class history to avoid dead loop. FST only accept regular grammer, and we are using
        # flag '*' for repeating. Hence, the class dependency graph should be a DAG.
        if name in class_history:
            raise BNFSyntaxError(
                f'found a reference cycle in gammar: {" -> ".join(class_history + [name])}')
        class_history = class_history.copy()
        class_history.append(name)

        rules = self._rule_set[name]
        dest_state = self._fst_writer.create_state()
        for rule in rules:
            state = self._generate_rule(rule, class_history, src_state)
            self._fst_writer.add_arc(state, dest_state, EPS_SYM, EPS_SYM)

        return dest_state

    def _generate_token(self, token: BNFToken, class_history: list[str], src_state: int) -> int:
        r''' generate FST for one token, returns the last state '''

        dest_state = src_state

        if token.type == BNFToken.SYMBOL:
            isymbols = self._get_symbols(token, 'i')
            osymbols = self._get_symbols(token, 'o')
            assert len(isymbols) == len(osymbols)

            for isym, osym in zip(isymbols, osymbols):
                state = self._fst_writer.create_state()
                self._fst_writer.add_arc(dest_state, state, isym, osym)
                dest_state = state

        elif token.type == BNFToken.I_SYMBOL:
            isymbols = self._get_symbols(token, 'i')
            for isym in isymbols:
                state = self._fst_writer.create_state()
                self._fst_writer.add_arc(dest_state, state, isym, EPS_SYM)
                dest_state = state

        elif token.type == BNFToken.O_SYMBOL:
            osymbols = self._get_symbols(token, 'o')
            for osym in osymbols:
                state = self._fst_writer.create_state()
                self._fst_writer.add_arc(dest_state, state, EPS_SYM, osym)
                dest_state = state

        elif token.type == BNFToken.CLASS:
            assert token.value
            dest_state = self._generate_class(token.value, class_history, dest_state)

        return dest_state

    def _generate_rule(self, rule: Rule, class_history: list[str], src_state: int) -> int:
        r''' generate FST from one single rule, returns the last state '''

        start_state = src_state
        if rule.flag == '*':
            # we need an additional state for repeat rules
            start_state = self._fst_writer.create_state()
            self._fst_writer.add_arc(src_state, start_state, EPS_SYM, EPS_SYM)

        # generate FST for each rule
        state = start_state
        for token in rule.tokens:
            state = self._generate_token(token, class_history, state)

        # add an epsilon arc from state to start_state if we have a repeat flag
        if rule.flag == '*':
            self._fst_writer.add_arc(state, start_state, EPS_SYM, EPS_SYM)
            state = start_state

        return state
