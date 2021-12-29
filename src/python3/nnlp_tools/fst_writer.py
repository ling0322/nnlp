from __future__ import annotations

import abc
from typing import TYPE_CHECKING, TextIO
from operator import itemgetter

from nnlp.symbol import EPS_SYM

NAN = float('nan')

if TYPE_CHECKING:
    FstArcTarget = tuple[int, int, float]

class FSTWriter(abc.ABC):
    r''' base class for Fst writer that supports add arc, add state and set final state '''

    @abc.abstractmethod
    def add_arc(
        self,
        src_state: int,
        dest_state: int,
        isymbol: str,
        osymbol: str,
        weight: float = 0.0,
    ) -> None:
        r''' 
        add an arc to Fst 
            Args:
            src_state (int): source state
            dest_state (int): destination state
            isymbol (str): input symbol
            osymbol (str): output symbol
            weight (float): weight'''
        pass

    @abc.abstractmethod
    def set_final_state(self, state: int, weight: float = 0.0) -> None:
        r''' set final state '''
        pass

    @abc.abstractmethod
    def create_state(self) -> int:
        r''' create a new state in FST, returns the state id '''
        pass

    @abc.abstractmethod
    def write(self) -> None:
        r''' finished Fst building, write all data into files '''
        pass


class TextFSTWriter(FSTWriter):
    r''' fst writer for OpenFST text file format
    FST arc was using OpenFST/AT&T FSM format: src dest ilabel olabel [weight]
    Args:
        fst_stream (TextIO): stream for writing AT&T FSM format FST
        ilabel_stream (TextIO): stream for writing input symbols 
        olabel_stream (TextIO): stream for writing output symbols 
        disambig_start_idx (int): start index for disambiguation symbols '''

    def __init__(self,
                 fst_stream: TextIO,
                 ilabel_stream: TextIO,
                 olabel_stream: TextIO) -> None:
        self._isymbols: dict[str, int] = {EPS_SYM: 0}
        self._osymbols: dict[str, int] = {EPS_SYM: 0}

        self._n_states = 1
        self._fst_stream: TextIO = fst_stream
        self._ilabel_stream: TextIO = ilabel_stream
        self._olabel_stream: TextIO = olabel_stream

        self._symbol_table_written = False

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

        isymbol_id = self._get_symbol_id(isymbol, self._isymbols)
        osymbol_id = self._get_symbol_id(osymbol, self._osymbols)

        # OpenFST/AT&T FSM format: src dest ilabel olabel [weight]
        self._fst_stream.write(f'{src_state} {dest_state} {isymbol_id} {osymbol_id} {weight}\n')

    def write(self) -> None:
        r''' implements ABC FstWriter '''

        if self._symbol_table_written:
            raise Exception(f'FST data already written')

        self._write_symbol_table(self._isymbols, self._ilabel_stream)
        self._write_symbol_table(self._osymbols, self._olabel_stream)

        self._symbol_table_written = True

    def _write_symbol_table(self, symbol_table: dict[str, int], stream: TextIO) -> None:
        ''' write symbol table to a stream '''

        symbols = list(symbol_table.items())
        symbols.sort(key=itemgetter(1))

        for symbol, symbol_id in symbols:
            stream.write(f'{symbol} {symbol_id}\n')

    def _get_symbol_id(self, symbol: str, symbol_dict: dict[str, int]) -> int:
        r''' get id of a input symbol from symbol_dict, it will create a new symbol id if 
        symbol not exist in symbol_dict '''

        if symbol == '':
            raise Exception(f'empty symbol is not supported, use EPS_SYM instead?')

        if symbol not in symbol_dict:
            symbol_id = len(symbol_dict)
            symbol_dict[symbol] = symbol_id
            return symbol_id
        else:
            return symbol_dict[symbol]
