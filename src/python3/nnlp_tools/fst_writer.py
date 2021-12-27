from __future__ import annotations

import abc
from typing import TYPE_CHECKING, TextIO
from operator import itemgetter

from nnlp.symbol import EPS_SYM_ID, MAX_SYMBOLS, NUM_RESERVED_SYM, UNK_SYM_ID, Disambig, Epsilon, Symbol, Unknown

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
        isymbol: Symbol,
        osymbol: Symbol,
        weight: float = 0.0,
    ) -> None:
        r''' 
        add an arc to Fst 
            Args:
            src_state (int): source state
            dest_state (int): destination state
            isymbol (Symbol): input symbol
            osymbol (Symbol): output symbol
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
        self._isymbols: dict[str, int] = {}
        self._osymbols: dict[str, int] = {}
        self._disambig_symbol_ids: set[int] = set()
        self._n_states = 1
        self._fst_stream: TextIO = fst_stream
        self._ilabel_stream: TextIO = ilabel_stream
        self._olabel_stream: TextIO = olabel_stream

        self._symbol_table_written = False
        self._disambig_start_idx = MAX_SYMBOLS

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
                isymbol: Symbol,
                osymbol: Symbol,
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

        self._write_eps_symbol(self._ilabel_stream)
        self._write_unk_symbol(self._ilabel_stream)
        self._write_symbol_table(self._isymbols, self._ilabel_stream)
        if self._disambig_symbol_ids:
            self._write_disambig_symbols(self._ilabel_stream)

        self._write_eps_symbol(self._olabel_stream)
        self._write_unk_symbol(self._olabel_stream)
        self._write_symbol_table(self._osymbols, self._olabel_stream)

        self._symbol_table_written = True

    def _write_unk_symbol(self, stream: TextIO) -> None:
        ''' write unknown symbol to stream '''

        stream.write(f'{self._generate_name("unk")} {UNK_SYM_ID}\n')

    def _write_eps_symbol(self, stream: TextIO) -> None:
        ''' write epsilon symbol to stream '''

        stream.write(f'{self._generate_name("eps")} {EPS_SYM_ID}\n')

    def _write_symbol_table(self, symbol_table: dict[str, int], stream: TextIO) -> None:
        ''' write symbol table to a stream '''

        symbols = list(symbol_table.items())
        symbols.sort(key=itemgetter(1))

        for symbol, symbol_id in symbols:
            stream.write(f'{symbol} {symbol_id}\n')

    def _write_disambig_symbols(self, stream: TextIO) -> None:
        ''' write disambiguation symbols to stream '''

        disambig_symbol_ids = list(self._disambig_symbol_ids)
        disambig_symbol_ids.sort()

        for symbol_id in disambig_symbol_ids:
            name = f'{symbol_id}'
            symbol = self._generate_name(name)
    
            stream.write(f'{symbol} {self._disambig_start_idx + symbol_id}\n')


    def _generate_name(self, name: str) -> str:
        ''' generate a symbol name that not conflict with current input and output symbol table '''

        prefix = ''
        final_name = f'#{prefix}{name}'
        while final_name in self._osymbols or final_name in self._isymbols:
            prefix += '_'
            final_name = f'#{prefix}{name}'

        return final_name

    def _get_symbol_id(self, symbol: Symbol, symbol_dict: dict[str, int]) -> int:
        r''' get id of a input symbol from symbol_dict, it will create a new symbol id if 
        symbol not exist in symbol_dict '''

        if isinstance(symbol, Disambig):
            self._disambig_symbol_ids.add(symbol.symbol_id)
            return self._disambig_start_idx + symbol.symbol_id
        elif isinstance(symbol, Epsilon):
            return EPS_SYM_ID
        elif isinstance(symbol, Unknown):
            return UNK_SYM_ID

        if symbol == '':
            raise Exception(f'empty symbol is not supported, use EPS_SYM instead?')

        if symbol not in symbol_dict:
            symbol_id = len(symbol_dict) + NUM_RESERVED_SYM
            if symbol_id == self._disambig_start_idx:
                raise Exception(f'too many input symbols (consider increase disambig_start_idx?)')

            symbol_dict[symbol] = symbol_id
            return symbol_id
        else:
            return symbol_dict[symbol]
