from __future__ import annotations

from collections import deque
from typing import Optional, Sequence, Union
import math

from .fst import Fst
from .symbol import EPS_SYM, UNK_SYM, Symbol, Unknown


class _Token:
    r''' token in decoding lattice '''

    def __init__(self, state: int, olabel: Symbol, prev_tok: Union[_Token, None],
                 cost: float) -> None:
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
    r''' beam-search decoder for WFST '''

    def __init__(self, fst: Fst, beam_size=8) -> None:
        self._fst = fst
        self._beam_size = beam_size

        self._beam: list[_Token]

        # mapping unknown symbol to real str value of input symbol
        self._unk_symbols: list[str] = []

    def decode_sequence(self, inputs: Sequence[str]) -> Sequence[str]:
        r''' decode the input sequence using Fst and return the best output sequence '''

        # initialize beam with start state
        self._beam = [_Token(0, EPS_SYM, None, 0)]

        # #unk_0 is never used
        self._unk_symbols = ['']

        symbol_inputs = self._process_inputs(inputs)

        for symbols in symbol_inputs:
            # prune beam
            self._prune_beam()

            # extend beam by processing epsilon arc from its tokens
            self._process_epsilon_arcs()

            # generate next frame of beam
            beam_agent: list[_Token] = []
            for symbol in symbols:
                self._process_symbol_arcs(symbol, beam_agent)
            self._beam = beam_agent

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

    def _process_inputs(self, inputs: Sequence[str]) -> Sequence[Sequence[Symbol]]:
        ''' process the inputs convert OOV to unknown token '''

        symbol_inputs: list[list[Symbol]] = []
        isymbol_dict = self._fst._isymbol_dict
        for symbol in inputs:
            symbols: list[Symbol] = []
            unk_id = len(self._unk_symbols)
            self._unk_symbols.append(symbol)
            symbols.append(Unknown(unk_id))
            if symbol in isymbol_dict:
                symbols.append(symbol)
            symbol_inputs.append(symbols)

        return symbol_inputs

    def _process_symbol_arcs(self, symbol: Symbol, beam_agent: list[_Token]) -> None:
        r''' generate next frame of beam '''

        if isinstance(symbol, str):
            for tok in self._beam:
                arcs = self._fst.get_arcs(tok.state, symbol)
                for arc in arcs:
                    dest_state, osymbol_id, weight = arc
                    osymbol = self._fst.get_osymbol(osymbol_id)
                    beam_agent.append(_Token(dest_state, osymbol, tok, tok.cost + weight))

        elif isinstance(symbol, Unknown):
            for tok in self._beam:
                arcs = self._fst.get_arcs(tok.state, UNK_SYM)
                for arc in arcs:
                    dest_state, osymbol_id, weight = arc
                    osymbol = self._fst.get_osymbol(osymbol_id)
                    if isinstance(osymbol, Unknown):
                        beam_agent.append(
                            _Token(dest_state, self._unk_symbols[symbol.symbol_id], tok,
                                   tok.cost + weight))
                    else:
                        beam_agent.append(_Token(dest_state, osymbol, tok, tok.cost + weight))
        
        else:
            raise Exception(f'unexpected symbol type')

    def _process_epsilon_arcs(self) -> None:
        r''' extend beam by processing epsilon arc from its tokens '''

        tok_queue = deque(self._beam)
        beam_agent: list[_Token] = []
        while tok_queue:
            tok = tok_queue.popleft()
            beam_agent.append(tok)

            arcs = self._fst.get_arcs(tok.state, EPS_SYM)
            for arc in arcs:
                dest_state, osymbol_id, weight = arc
                osymbol = self._fst.get_osymbol(osymbol_id)
                tok_queue.append(_Token(dest_state, osymbol, tok, tok.cost + weight))
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
