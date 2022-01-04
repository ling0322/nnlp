from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Optional, Union, TextIO
from operator import itemgetter

from nnlp.symbol import EPS_SYM
from .util import read_symbol_table

NAN = float('nan')

if TYPE_CHECKING:
    FstArcTarget = tuple[int, int, float]

class FstWriter:
    r''' fst writer for OpenFST text file format
    FST arc was using OpenFST/AT&T FSM format: src dest ilabel olabel [weight]
    Args:
        fst_stream (TextIO): stream for writing AT&T FSM format FST
        ilabel_file (TextIO|str): if it's a file-like object, write input symbols to it, if it's
                                  a str, read the isymbol table from it (all isymbol in add_arc
                                  should exist in this file). 
        olabel_file (TextIO|str): stream or file for output symbols (other behavior is the same as
                                  ilabel_file) '''

    # symbol table for input and output symbols
    _isymbols: dict[str, int]
    _osymbols: dict[str, int]

    # output stream for input and outpue symbol table file
    _ilabel_stream: Optional[TextIO]
    _olabel_stream: Optional[TextIO]
 
    def __init__(self,
                 fst_stream: TextIO,
                 ilabel_file: Union[TextIO, str],
                 olabel_file: Union[TextIO, str]) -> None:

        if isinstance(ilabel_file, str):
            self._isymbols = read_symbol_table(ilabel_file)
            self._isymbols_readonly = True
            self._ilabel_stream = None
        else:
            self._isymbols = {EPS_SYM: 0}
            self._ilabel_stream = ilabel_file
            self._isymbols_readonly = False
    
        if isinstance(olabel_file, str):
            self._osymbols = read_symbol_table(olabel_file)
            self._osymbols_readonly = True
            self._olabel_stream = None
        else:
            self._osymbols = {EPS_SYM: 0}
            self._olabel_stream = olabel_file
            self._osymbols_readonly = False

        self._n_states = 1
        self._fst_stream: TextIO = fst_stream

        self._symbol_table_written = False

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        ''' write symbol table before exit '''

        if exc_type == None and not self._symbol_table_written:
            self.write()

    def __del__(self):
        ''' make sure write() is called '''

        if not self._symbol_table_written:
            print(f"warning: FstWriter: write() not called")

    def create_state(self) -> int:
        r''' implements ABC FstWriter '''

        self._n_states += 1
        return self._n_states - 1

    def set_final_state(self, state: int, weight: float = 0.0) -> None:
        r''' implements ABC FstWriter '''

        # OpenFST/AT&T FSM format: state [weight]
        self._fst_stream.write(f'{state} {weight}\n')

    def add_arc(self,
                src_state: int,
                dest_state: int,
                isymbol: str,
                osymbol: str,
                weight: float = 0.0) -> None:
        r''' implements ABC FstWriter '''

        isymbol_id = self._get_symbol_id(isymbol, self._isymbols, self._isymbols_readonly)
        osymbol_id = self._get_symbol_id(osymbol, self._osymbols, self._osymbols_readonly)

        # OpenFST/AT&T FSM format: src dest ilabel olabel [weight]
        self._fst_stream.write(f'{src_state} {dest_state} {isymbol_id} {osymbol_id} {weight}\n')

    def write(self) -> None:
        r''' implements ABC FstWriter '''

        if self._symbol_table_written:
            raise Exception(f'FST data already written')

        if self._ilabel_stream:
            self._write_symbol_table(self._isymbols, self._ilabel_stream)
        if self._olabel_stream:
            self._write_symbol_table(self._osymbols, self._olabel_stream)

        self._symbol_table_written = True

    @staticmethod
    def _write_symbol_table(symbol_table: dict[str, int], stream: TextIO) -> None:
        ''' write symbol table to a stream '''

        symbols = list(symbol_table.items())
        symbols.sort(key=itemgetter(1))

        for symbol, symbol_id in symbols:
            stream.write(f'{symbol} {symbol_id}\n')

    def _get_symbol_id(self, symbol: str, symbol_dict: dict[str, int], readonly: bool) -> int:
        ''' get id of a input symbol from symbol_dict. When readonly is False, it will create a new
        symbol id for nonexisting symbols, otherwise, it will raise an Exception '''

        if symbol == '':
            raise Exception(f'empty symbol is not supported, use EPS_SYM instead?')

        if symbol not in symbol_dict:
            if not readonly:
                symbol_id = len(symbol_dict)
                symbol_dict[symbol] = symbol_id
                return symbol_id
            else:
                raise Exception(f'symbol not exist: {symbol}')
        else:
            return symbol_dict[symbol]
