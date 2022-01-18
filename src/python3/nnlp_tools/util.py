from __future__ import annotations

import math
from operator import itemgetter
from typing import TYPE_CHECKING

from nnlp.symbol import escape_symbol

if TYPE_CHECKING:
    from .lexicon_fst_builder import Lexicon
    from .rule import Rule


class BNFSyntaxError(Exception):
    ''' raised when an invaid BNF expression string occured '''
    pass


def read_lexicon(filename: str, is_escaped: bool) -> Lexicon:
    ''' 
    read lexicon from file, the lexicon format is:
        <word> <probability> <symbol1> <symbol2> ... <symbolN>\\n 
    it will also escape symbols and words using escape_symbol()
    Args:
        filename: filename of the lexicon
        is_escaped (bool): true if the lexicon is escaped '''

    lexicon: Lexicon = []
    with open(filename, encoding='utf-8') as f:
        for line in f:
            try:
                row = line.strip().split()
                assert len(row) >= 3
                if is_escaped:
                    word = row[0]
                    symbols = list(row[2:])
                else:
                    word = escape_symbol(row[0])
                    symbols = list(map(escape_symbol, row[2:]))
                weight = -math.log(float(row[1]))

                lexicon.append((word, symbols, weight))
            except Exception as _:
                raise Exception(
                    f'unexpected line in {filename}: {line.strip()}')

    return lexicon

def lexicon_add_ilabel_selfloop(lexicon: Lexicon) -> Lexicon:
    ''' add missing single input label selfloop to lexicon. It could speed up
    decoding process for handling <unk> symbol
    '''
    # all input symbols
    vocab: set[str] = set()

    # the input symbols that already have selfloop in lexicon
    selfloop_syms = set()

    max_weight = 0
    for _, isyms, _ in lexicon:
        vocab.update(isyms)
        if len(isyms) == 1:
            selfloop_syms.add(isyms[0])

    max_weight = max(map(itemgetter(2), lexicon))
    asl_weight = max_weight - math.log(0.1)
    asl_lexicon: Lexicon = lexicon.copy()

    isymbols = list(vocab)
    isymbols.sort()
    for symbol in isymbols:
        if symbol not in selfloop_syms:
            asl_lexicon.append((symbol, (symbol,), asl_weight))

    return asl_lexicon


class SourcePosition:
    r''' represent a position in source file, usually it is (filename, line number)  '''

    def __init__(self, fileanme: str = None, line: int = None):
        self._filename = fileanme
        self._line = line
