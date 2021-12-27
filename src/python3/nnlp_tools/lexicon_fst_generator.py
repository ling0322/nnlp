''' generate FST from lexicon '''
from __future__ import annotations
from typing import Optional, Sequence, TYPE_CHECKING, Type, Union
import math
import sys

from nnlp.symbol import EPS_SYM, UNK_SYM, Symbol
from nnlp.fst import Disambig
from nnlp_tools.fst_writer import FSTWriter

if TYPE_CHECKING:
    Lexicon = list[tuple[str, Sequence[str], float]]
    DisambigLexicon = list[tuple[str, Sequence[Symbol], float]]

class LexiconFSTGenerator:
    r''' generate FST from lexicon '''

    def __call__(self,
                 lexicon: Lexicon,
                 fst_writer: FSTWriter,
                 unknown_symbol: str = 'fail') -> DisambigLexicon:
        ''' 
        generate FST from lexicon, and write the FST to file using fst_writer
        Args:
            lexicon: lexicon with (word, symbols, weight) pair
            fst_writer (FstWriter): the fst writer
            unknown_symbol (str): behavior for unknown symbol. 
                                  output: output the symbol itself
                                  ignore: ignore this symbol
                                  fail: do not add logic to handle unknown symbols, and decoding
                                        will fail when an unknown symbol occured
        Returns:
            intermediate lexicon after adding diambig symbols'''

        disambig_lexicon = self._add_disambig(lexicon)

        min_weight = float('inf')
        unk_factor = -round(math.log(0.1), 3)
        for word, symbols, weight in disambig_lexicon:
            state = 0
            if min_weight > weight:
                min_weight = weight

            for idx, symbol in enumerate(symbols):
                # back to state 0 if ch is the last char in word
                arc_weight = weight if idx == 0 else 0
                next_state = 0 if idx == len(symbols) - 1 else fst_writer.create_state()
                osymbol: Symbol = word if idx == 0 else EPS_SYM

                fst_writer.add_arc(state, next_state, symbol, osymbol, arc_weight)
                state = next_state

        # handle unknown symbol
        if unknown_symbol == 'output':
            fst_writer.add_arc(0, 0, UNK_SYM, UNK_SYM, min_weight + unk_factor)
        elif unknown_symbol == 'ignore':
            fst_writer.add_arc(0, 0, UNK_SYM, EPS_SYM, min_weight + unk_factor)
        elif unknown_symbol == 'fail':
            # do not add the arcs for unknown symbol
            pass
        else:
            raise Exception(f'unexpected value for unknown_symbol: {unknown_symbol}')

        fst_writer.set_final_state(0)
        fst_writer.write()

        return disambig_lexicon

    def _add_disambig(self, lexicon: Lexicon) -> DisambigLexicon:
        ''' add disambiguation symbols to lexicon in order to make make decoding graphs
        determinizable. It adds disambiguation symbols #1, #2, #3, ... to the end of symbols to
        make sure that all symbols are different and none was prefix of another
        Args:
            lexicon: input lexicon
        Returns:
            lexicon after adding disambiguation symbols '''

        disambig_lexicon: DisambigLexicon = []

        # compute prefix and disambiguation set
        prefix: set[tuple[str, ...]] = set()
        vocab: set[tuple[str, ...]] = set()
        ambig: set[tuple[str, ...]] = set()
        for _, symbols, _ in lexicon:
            symbols = tuple(symbols)
            for idx in range(1, len(symbols)):
                prefix.add(tuple(symbols[:idx]))

            if symbols in vocab:
                ambig.add(symbols)
            vocab.add(symbols)

        # free vocab        
        vocab = set()

        disambig: dict[tuple[str, ...], int] = {}
        for word, symbols, weight in lexicon:
            symbols = tuple(symbols)
            disambig_symbols: tuple[Union[str, Disambig], ...] = tuple(symbols)
            if symbols in disambig:
                disambig[symbols] += 1
                disambig_symbols += (Disambig(disambig[symbols]),)
            elif symbols in prefix or symbols in ambig:
                disambig[symbols] = 1
                disambig_symbols += (Disambig(disambig[symbols]),)
            else:
                disambig[symbols] = 0

            disambig_lexicon.append((word, disambig_symbols, weight))

        return disambig_lexicon
