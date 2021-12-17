''' generate FST from lexicon '''
from __future__ import annotations
from typing import Sequence, TYPE_CHECKING, Type, Union

from .symbol import EPS_SYM, Symbol
from .fst import Disambig, FSTWriter

if TYPE_CHECKING:
    Lexicon = list[tuple[str, Sequence[str], float]]
    DisambigLexicon = list[tuple[str, Sequence[Union[str, Disambig]], float]]



class LexiconFSTGenerator:
    r''' generate FST from lexicon '''

    def __call__(self,
                 lexicon: Lexicon,
                 fst_writer: FSTWriter,
                 unknown_symbol: str = 'output') -> None:
        ''' 
        generate FST from lexicon, and write the FST to file using fst_writer
        Args:
            lexicon: lexicon with (word, symbols, weight) pair
            fst_writer (FstWriter): the fst writer
            unknown_symbol (str): behavior for unknown symbol. 
                                  output: output the symbol itself
                                  ignore: ignore this symbol
                                  fail: do not add logic to handle unknown symbols, and decoding
                                        will fail when an unknown symbol occured '''

        disambig_lexicon = self._add_disambig(lexicon)

        for word, symbols, weight in disambig_lexicon:
            state = 0
            for idx, symbol in enumerate(symbols):
                # back to state 0 if ch is the last char in word
                arc_weight = weight if idx == 0 else 0
                next_state = 0 if idx == len(word) - 1 else fst_writer.create_state()
                osymbol: Symbol = word if idx == 0 else EPS_SYM

                fst_writer.add_arc(state, next_state, symbol, osymbol, arc_weight)
                state = next_state


        fst_writer.set_final_state(0)
        fst_writer.write()

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
            for idx in range(len(symbols) - 1):
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
