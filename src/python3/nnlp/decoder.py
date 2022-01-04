from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Optional, Sequence, Union
import math

from .fst import Fst
from .symbol import BRK_SYM, CAP_EPS_SYM, EPS_SYM, UNK_SYM, CAP_SYM, escape_symbol, is_special_symbol, unescape_symbol
if TYPE_CHECKING:
    InputSymbol = Union[str, tuple[str, str]]


class _Token:
    r''' token in decoding lattice '''

    def __init__(self,
                 state: int,
                 olabel: str,
                 prev_tok: Union[_Token, None],
                 cost: float,
                 capture: Optional[str] = None) -> None:
        self.state = state
        self.olabel = olabel
        self.prev_token = prev_tok
        self.cost = cost
        self.capture = capture

    def __lt__(self, tok) -> bool:
        if not isinstance(tok, _Token):
            return False
        return self.cost < tok.cost

    def __repr__(self) -> str:
        return f'_Token({self.state}, "{self.olabel}", cost={self.cost}, capture={self.capture})'


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

        for symbol in symbol_inputs:
            # prune beam
            self._prune_beam()

            # extend beam by processing epsilon arc from its tokens
            self._process_epsilon_arcs()

            # generate next frame of beam
            beam_agent: list[_Token] = []
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
        osymbols, captures = self._best_path()
        
        return self._process_outputs(osymbols, captures)

    def _prune_beam(self) -> None:
        r''' prune beam to self._beam_size '''

        self._beam.sort()
        self._beam = self._beam[:self._beam_size]

    def _process_inputs(self, inputs: Sequence[str]) -> Sequence[InputSymbol]:
        ''' 
        process the inputs, do following things
          - escape input symbols
          - for OOV, replace it with (UNK_SYM, OOV-word)
        '''

        symbol_inputs: list[InputSymbol] = []
        isymbol_dict = self._fst._isymbol_dict
        for symbol in inputs:
            symbol = escape_symbol(symbol)
            if symbol not in isymbol_dict:
                symbol_inputs.append((UNK_SYM, symbol))
            else:
                symbol_inputs.append(symbol)

        return symbol_inputs

    def _process_outputs(self, output_symbols: list[str], capture_symbols: list[str]) -> list[str]:
        ''' process the outputs generated by best path, it will remove <eps> and <capture_eps>,
        and fill <capture> with capture_symbols '''

        outputs: list[str] = []
        capture_queue = deque(capture_symbols)
        for symbol in output_symbols:
            if is_special_symbol(symbol):
                if symbol == EPS_SYM:
                    # just remove eps symbols
                    pass
                elif symbol == CAP_SYM:
                    # append a capture symbol
                    if not capture_queue:
                        raise Exception(f'capture mismatch')
                    capture_symbol = capture_queue.popleft()
                    outputs.append(capture_symbol)
                elif symbol == CAP_EPS_SYM:
                    # do nothing, just de-queue a capture symbol and ignore it 
                    if not capture_queue:
                        raise Exception(f'capture mismatch')
                    capture_symbol = capture_queue.popleft()
                elif symbol in {BRK_SYM}:
                    # symbols to output
                    outputs.append(unescape_symbol(symbol))
                else:
                    raise Exception(f'unexpected output symbol: {symbol}')
            else:
                outputs.append(unescape_symbol(symbol))
        
        # number of <capture> and <capture_eps> should always match the length of capture_symbols
        if capture_queue:
            raise Exception(f'capture mismatch')
        
        return outputs

    def _process_symbol_arcs(self, symbol: InputSymbol, beam_agent: list[_Token]) -> None:
        r''' generate next frame of beam '''

        if isinstance(symbol, str):
            for tok in self._beam:
                arcs = self._fst.get_arcs(tok.state, symbol)
                for arc in arcs:
                    dest_state, osymbol, weight = arc
                    beam_agent.append(_Token(dest_state, osymbol, tok, tok.cost + weight))

        elif isinstance(symbol, tuple) and symbol[0] == UNK_SYM:
            for tok in self._beam:
                arcs = self._fst.get_arcs(tok.state, UNK_SYM)
                for arc in arcs:
                    dest_state, osymbol, weight = arc
                    beam_agent.append(
                        _Token(dest_state, osymbol, tok, tok.cost + weight, capture=symbol[1]))

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
                dest_state, osymbol, weight = arc
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

    def _best_path(self) -> tuple[list[str], list[str]]:
        r''' get best path from beam returns (output symbols, captured symbols) '''

        symbols: list[str] = []
        captures: list[str] = []
        best_tok: Optional[_Token] = min(self._beam)
        while best_tok:
            symbols.append(best_tok.olabel)
            if best_tok.capture:
                captures.append(best_tok.capture)
            best_tok = best_tok.prev_token

        symbols.reverse()
        captures.reverse()

        return (symbols, captures)
