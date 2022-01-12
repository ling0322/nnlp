

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from nnlp.symbol import escape_symbol

if TYPE_CHECKING:
    from .lexicon_fst_builder import Lexicon
    from .rule import Rule

class BNFSyntaxError(Exception):
    ''' raised when an invaid BNF expression string occured '''
    pass

def read_symbol_table(symbols_file: str) -> dict[str, int]:
    ''' read symbol table from file '''

    symbol_table: dict[str, int] = {}
    with open(symbols_file, encoding='utf-8') as f:
        for line in f:
            row = line.strip().split()
            if len(row) != 2:
                raise Exception(f'invalid line in symbol_stream: {line.strip()}')
            symbol: str = row[0]
            symbol_id = int(row[1])

            symbol_table[symbol] = symbol_id

    return symbol_table

def read_lexicon(filename: str, is_escaped: bool) -> Lexicon:
    ''' 
    read lexicon from file, the lexicon format is:
        <word> <probability> <symbol1> <symbol2> ... <symbolN>\\n 
    it will also escape symbols and words using escape_symbol()
    Args:
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
                raise Exception(f'unexpected line in {filename}: {line.strip()}')

    return lexicon

class SourcePosition:
    r''' represent a position in source file, usually it is (filename, line number)  '''
    def __init__(self, fileanme: str = None, line: int = None):
        self._filename = fileanme
        self._line = line



