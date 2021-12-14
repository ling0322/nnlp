''' generate FST from lexicon '''
from __future__ import annotations

from .fst import EPS_SYM, FstWriter

class LexiconFSTGenerator:
    r''' generate FST from lexicon '''

    def __call__(self, lexicon: list[tuple[str, float]], fst_writer: FstWriter) -> None:
        r''' generate FST from lexicon, and write the FST to file using fst_writer
             Args:
                 lexicon (list[tuple[str, float]]): lexicon with (word, weight) pair
                 fst_writer (FstWriter): the fst writer'''

        for word, weight in lexicon:
            state = 0
            for idx, ch in enumerate(word):
                # back to state 0 if ch is the last char in word
                next_state = 0 if idx == len(word) - 1 else fst_writer.create_state()
                osymbol = word if idx == 0 else EPS_SYM

                fst_writer.add_arc(state, next_state, ch, osymbol, weight)
                state = next_state

        fst_writer.set_final_state(0)
        fst_writer.write()
