''' generate FST from lexicon '''
from __future__ import annotations
from typing import Sequence, TYPE_CHECKING

from nnlp.symbol import EPS_SYM, make_disambig_symbol
from .mutable_fst import MutableFst

if TYPE_CHECKING:
    Lexicon = list[tuple[str, Sequence[str], float]]


def build_lexicon_fst(lexicon: Lexicon, name: str = 'L') -> MutableFst:
    '''
    Build a FST for input lexicon, returns the MutableFst. it will add disambig
    symbols automatically
    Args:
        lexicon: The input lexicon
    Returns:
        the FST for lexicon (after add disambig symbols)
    '''

    mutable_fst = MutableFst(name=name)
    fst_builder = LexiconFstBuilder()
    fst_builder(lexicon, mutable_fst)

    return mutable_fst


class LexiconFstBuilder:
    r''' generate FST from lexicon '''

    def __call__(self, lexicon: Lexicon, mutable_fst: MutableFst) -> Lexicon:
        ''' 
        build FST from lexicon, and write the FST to file using fst_writer
        Args:
            lexicon: lexicon with (word, symbols, weight) pair
            fst_writer (FstWriter): the fst writer
        Returns:
            intermediate lexicon after adding diambig symbols'''

        disambig_lexicon = self._add_disambig(lexicon)
        for word, symbols, weight in disambig_lexicon:
            state = 0
            if not word or not symbols:
                raise Exception(
                    f'invalid lexicon entry: {(word, symbols, weight)}')

            for idx, symbol in enumerate(symbols):
                # back to state 0 if ch is the last char in word
                arc_weight = weight if idx == 0 else 0
                next_state = 0 if idx == len(
                    symbols) - 1 else mutable_fst.create_state()
                osymbol: str = word if idx == 0 else EPS_SYM

                mutable_fst.add_arc(state, next_state, symbol, osymbol,
                                    arc_weight)
                state = next_state

        mutable_fst.set_final_state(0)

        return disambig_lexicon

    def _add_disambig(self, lexicon: Lexicon) -> Lexicon:
        ''' add disambiguation symbols to lexicon in order to make make decoding graphs
        determinizable. It adds disambiguation symbols #1, #2, #3, ... to the end of symbols to
        make sure that all symbols are different and none was prefix of another
        Args:
            lexicon: input lexicon
        Returns:
            lexicon after adding disambiguation symbols '''

        disambig_lexicon: Lexicon = []

        # compute prefix and disambiguation set
        prefix: set[tuple[str, ...]] = set()
        all_symbol_seq: set[tuple[str, ...]] = set()
        ambig_symbol_seq: set[tuple[str, ...]] = set()
        for _, symbols, _ in lexicon:
            symbols = tuple(symbols)
            for idx in range(1, len(symbols)):
                prefix.add(tuple(symbols[:idx]))

            if symbols in all_symbol_seq:
                ambig_symbol_seq.add(symbols)
            all_symbol_seq.add(symbols)

        # free all_symbol_seq
        all_symbol_seq = set()

        disambig: dict[tuple[str, ...], int] = {}
        for word, symbols, weight in lexicon:
            symbols = tuple(symbols)
            disambig_symbols: tuple[str, ...] = tuple(symbols)
            if symbols in disambig:
                disambig[symbols] += 1
                disambig_symbols += (make_disambig_symbol(disambig[symbols]),)
            elif symbols in prefix or symbols in ambig_symbol_seq:
                disambig[symbols] = 1
                disambig_symbols += (make_disambig_symbol(disambig[symbols]),)
            else:
                disambig[symbols] = 0

            disambig_lexicon.append((word, disambig_symbols, weight))

        return disambig_lexicon
