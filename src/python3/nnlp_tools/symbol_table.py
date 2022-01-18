''' SymbolTable stores the mapping table between symbol-id and symbol '''
from __future__ import annotations

import pywrapfst
from typing import Iterator, Union
from nnlp.symbol import EPS_SYM


class SymbolTable:
    ''' wrapper for pywrapfst.SymbolTable '''

    def __init__(self):
        self._symbol_table = pywrapfst.SymbolTable()
        self._symbol_table.add_symbol(EPS_SYM, 0)

    def __contains__(self, o: Union[int, str]) -> str:
        ''' returns true if symbol or symbol-id exists '''
        return self._symbol_table.member(o)

    def __iter__(self) -> Iterator[tuple[int, str]]:
        '''
        iterate all symbols
        Returns:
            Iterator of (symbol-id, symbol)
        '''
        return self._symbol_table.__iter__()

    def copy(self) -> SymbolTable:
        ''' makes a copy of the symbol table '''
        symbol_table = SymbolTable()
        symbol_table._symbol_table = self._symbol_table.copy()
        return symbol_table

    def add_symbol(self, symbol: str) -> int:
        ''' add a symbol and returns its symbol-id '''
        return self._symbol_table.add_symbol(symbol)

    def get_id(self, symbol: str) -> int:
        ''' find id by symbol, raise KeyError if not found '''

        symbol_id = self._symbol_table.find(symbol)
        if symbol_id == pywrapfst.NO_LABEL:
            raise KeyError(symbol)

        return symbol_id

    def get_symbol(self, symbol_id: int) -> str:
        ''' find symbol by symbol-id, raise KeyError if not found '''

        value = self._symbol_table.find(symbol_id)
        if value == '':
            raise KeyError(symbol_id)

        return value

    def write_text(self, filename: str):
        ''' write the SymbolTable to text file '''
        self._symbol_table.write_text(filename)
