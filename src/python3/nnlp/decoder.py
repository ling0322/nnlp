from __future__ import annotations

from collections import deque
from typing import IO, Deque, Optional, Sequence, Union
import math
import unittest
import io

from .bnf_tokenizer import BNFTokenizer
from .fst_generator import FSTGenerator
from .rule_parser import RuleParser
from .util import SourcePosition, generate_rule_set

from .fst import Fst, TextFSTWriter
from .symbol import EPS_SYM, Symbol

class _Token:
    r''' token in decoding lattice '''

    def __init__(self, state: int, olabel: Symbol, prev_tok: Union[_Token, None], cost: float) -> None:
        self.state = state
        self.olabel = olabel
        self.prev_token = prev_tok
        self.cost = cost

    def __lt__(self, tok) -> bool:
        if not isinstance(tok, _Token):
            return False
        return self.cost < tok.cost

    def __repr__(self) -> str:
        return f'_Token({self.state}, "{self.olabel}", cost={self.cost})'


class FstDecoder:
    r''' beam-search decoder fpr WFST '''

    def __init__(self, fst: Fst, beam_size=8) -> None:
        self._fst = fst
        self._beam_size = beam_size

        self._beam: list[_Token]

    def decode_sequence(self, inputs: Sequence[str]) -> Sequence[str]:
        r''' decode the input sequence using Fst and return the best output sequence '''

        # initialize beam with start state
        self._beam = [_Token(0, EPS_SYM, None, 0)]

        for symbol in inputs:
            # prune beam
            self._prune_beam()

            # extend beam by processing epsilon arc from its tokens
            self._process_epsilon_arcs()

            # generate next frame of beam
            self._process_symbol_arcs(symbol)

            # early exit if no state in beam
            if not self._beam:
                return []

        # add final weights to active tokens in beam
        self._add_final_weights()

        # early exit if no state in beam
        if not self._beam:
            return []

        # get best path
        return self._get_best_path()

    def _prune_beam(self) -> None:
        r''' prune beam to self._beam_size '''

        self._beam.sort()
        self._beam = self._beam[:self._beam_size]

    def _process_symbol_arcs(self, symbol: str) -> None:
        r''' generate next frame of beam '''

        beam_agent: list[_Token] = []
        for tok in self._beam:
            arcs = self._fst.get_arcs(tok.state, symbol)
            for arc in arcs:
                beam_agent.append(_Token(arc.dest_state, arc.osymbol, tok, tok.cost - arc.weight))

        self._beam = beam_agent

    def _process_epsilon_arcs(self) -> None:
        r''' extend beam by processing epsilon arc from its tokens '''

        tok_queue = deque(self._beam)
        beam_agent: list[_Token] = []
        while tok_queue:
            tok = tok_queue.popleft()
            beam_agent.append(tok)

            arcs = self._fst.get_arcs(tok.state, EPS_SYM)
            for arc in arcs:
                tok_queue.append(_Token(arc.dest_state, arc.osymbol, tok, tok.cost - arc.weight))
        self._beam = beam_agent

    def _add_final_weights(self) -> None:
        r''' for each token in self._beam, if it is a final state, add final costs to it. If not, just
        remove it from beam '''

        self._process_epsilon_arcs()
        beam_agent: list[_Token] = []
        for tok in self._beam:
            cost = -self._fst.get_final_weight(tok.state)
            if not math.isnan(cost):
                tok.cost += cost
                beam_agent.append(tok)
        self._beam = beam_agent

    def _get_best_path(self) -> Sequence[str]:
        r''' get best path from beam returns its output symbols '''

        symbols: list[str] = []
        best_tok: Optional[_Token] = min(self._beam)
        while best_tok:
            if isinstance(best_tok.olabel, str):
                symbols.append(best_tok.olabel)
            best_tok = best_tok.prev_token
        symbols.reverse()

        return symbols
